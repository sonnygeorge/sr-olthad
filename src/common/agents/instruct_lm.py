import asyncio
import logging
import warnings
from collections import Counter
from functools import partial
from json import JSONDecodeError
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from common.schema import (
    Agent,
    InstructLm,
    InstructLmChatRole,
    InstructLmMessage,
    LmStreamHandler,
    LmStreamsHandler,
)
from common.utils import (
    call_or_await,
    detect_extract_and_parse_json_from_text,
    get_semaphore_bound_coroutine,
)


class LmRetryHandler(Protocol):
    def __call__(idx: int, msg: str) -> None: ...


LmJsonOutputModelT = TypeVar("LmJsonOutputModelT", bound=BaseModel)


class InstructLmAgentOutput(BaseModel, Generic[LmJsonOutputModelT]):
    """
    Output object for an InstructLmAgent.

    Attributes:
        data (LmJsonOutputModelT): The parsed Pydantic BaseModel from the LM's output JSON.
        messages (list[InstructLmMessage] | list[list[InstructLmMessage]]): The list of
            messages from the full LM chat (or list of multiple of such chats in the case
            of having run self-consistency 'voting').

    TODO: Add a way to return all LM messages that were unparsable in order to save them
        as 'bad' examples to a fine-tuning dataset.
    """

    data: LmJsonOutputModelT
    # NOTE: Nested list in the case of multiple calls for voting
    messages: list[InstructLmMessage] | list[list[InstructLmMessage]]


class InstructLmAgentRunMethod(Protocol):
    """
    Protocol for type-hinting when something should be an InstructLmAgent instance's
    run method.
    """

    async def __call__(
        self,
        input_messages: list[InstructLmMessage],
        retry_callback: LmRetryHandler | None = None,
        **kwargs,
    ) -> InstructLmAgentOutput[LmJsonOutputModelT]:
        pass


class AggregateWinningVoteReasons(Protocol):
    """
    Protocol for strategies that aggregate multiple 'vote reasons' (in self-consistency
    multi-sample 'voting') into a single aggregate 'reason' string.
    """

    def __call__(
        self,
        winning_reasons: list[str],
        winner: str,
        num_winning_votes: int,
        num_total_votes: int,
    ) -> str:
        pass


# NOTE: Implementation of protocol `AggregateWinningVoteReasons`
def _default_aggregate_winning_vote_reasons(
    winning_reasons: list[str], winner: str, num_winning_votes: int, num_total_votes: int
) -> str:
    """
    The default strategy implementation of the AggregateWinningVoteReasons protocol that
    renders information into a basic hard-coded f-string.
    """
    return (
        f"'{winner}' was chosen since, in a multi-agent vote, it received {num_winning_votes}"
        f"/{num_total_votes} votes for the following reasons:\n{winning_reasons}"
    )


class InstructLmAgent(Agent, Generic[LmJsonOutputModelT]):
    """
    An agent that queries an instruct LM with input messages and parses the LM response
    using the specified `response_json_model` Pydantic model.
    """

    def __init__(  # TODO: Docstring
        self,
        instruct_lm: InstructLm,
        response_json_model: type[LmJsonOutputModelT],
        max_tries_to_get_parsable_response: int = 1,
        num_calls_for_voting: int = 1,
        max_async_calls: int | None = None,
        vote_field: str | None = None,
        reason_field: str | None = None,
        aggregate_winning_vote_reasons: AggregateWinningVoteReasons = _default_aggregate_winning_vote_reasons,
        streams_handler: LmStreamsHandler | None = None,
        logger: logging.Logger | None = None,
    ):
        super().__init__()

        if num_calls_for_voting > 1:
            if vote_field is None:
                raise ValueError("If num_calls_for_voting > 1, vote_field is required.")
            if reason_field is None:
                # The response_json_model must only have the vote field
                if set(response_json_model.model_fields.keys()) != {vote_field}:
                    raise ValueError(
                        "If not specifying the reason_field, the vote_field must be the "
                        "only field in the output json model."
                    )
            # Else, the response_json_model must only have the vote and reason fields
            elif set(response_json_model.model_fields.keys()) != {vote_field, reason_field}:
                raise ValueError(
                    "If specifying both the vote and reason fields, these "
                    "must be the only fields of the output json model."
                )

        self.instruct_lm = instruct_lm
        self.output_data_model = response_json_model
        self.max_tries_to_get_parsable_response = max_tries_to_get_parsable_response
        self.num_calls_for_voting = num_calls_for_voting
        self.max_async_calls = max_async_calls
        self.vote_field = vote_field
        self.reason_field = reason_field
        self.aggregate_winning_vote_reasons = aggregate_winning_vote_reasons
        self.streams_handler = streams_handler
        self.logger = logger

    def _warn(self, msg: str) -> None:
        if self.logger is not None:
            self.logger.warning(msg)
        else:
            warnings.warn(msg, stacklevel=2)

    async def _get_response_and_parse_with_retry(
        self,
        input_messages: list[InstructLmMessage],
        retry_callback: LmRetryHandler | None = None,
        stream_handler: LmStreamsHandler | None = None,
        call_idx: int = 0,
        **kwargs,  # kwargs passed through to the InstructLm.generate method
    ) -> tuple[LmJsonOutputModelT, str]:
        tries_left = self.max_tries_to_get_parsable_response
        while tries_left > 0:
            try:
                response = await self.instruct_lm.generate(
                    messages=input_messages, stream_handler=stream_handler, **kwargs
                )
                output_data = detect_extract_and_parse_json_from_text(
                    text=response, model_to_extract=self.output_data_model
                )
                return output_data, response
            # TODO: Change `Exception` to specific exceptions
            except (ValidationError, JSONDecodeError, Exception) as e:
                if tries_left == 1:
                    raise e
                tries_left -= 1
                msg = f"Failed to get a parsable response: {e}, {tries_left} tries remaining"
                self._warn(msg)
                if retry_callback is not None:
                    await call_or_await(retry_callback, call_idx, msg)

    async def _run(
        self,
        input_messages: list[InstructLmMessage],
        retry_callback: LmRetryHandler | None = None,
        stream_handler: LmStreamHandler | None = None,
        call_idx: int = 0,
        **kwargs,  # kwargs passed through to the InstructLm.generate method
    ) -> InstructLmAgentOutput[LmJsonOutputModelT]:
        # Get parsed response
        output_data, response = await self._get_response_and_parse_with_retry(
            input_messages=input_messages,
            retry_callback=retry_callback,
            stream_handler=stream_handler,
            call_idx=call_idx,
            **kwargs,
        )
        # Add assistant message to input message
        messages = input_messages + [
            InstructLmMessage(role=InstructLmChatRole.ASSISTANT, content=response)
        ]
        # Return output
        return InstructLmAgentOutput(data=output_data, messages=messages)

    async def _run_with_voting(
        self,
        input_messages: list[InstructLmMessage],
        retry_callback: LmRetryHandler | None = None,
        streams_handler: LmStreamsHandler | None = None,
        **kwargs,  # kwargs passed through to the InstructLm.generate method
    ) -> InstructLmAgentOutput[LmJsonOutputModelT]:
        # Prepare coroutines
        semaphore = asyncio.Semaphore(self.max_async_calls)
        coroutines = []
        for coroutine_idx in range(self.num_calls_for_voting):
            if self.streams_handler is not None:
                # Turn it into a single stream handler by binding the stream_idx
                stream_handler = partial(streams_handler, stream_idx=coroutine_idx)
            else:
                stream_handler = None
            # Ensure the coroutine is bound to the semaphore
            semaphore_bounded_coroutine = get_semaphore_bound_coroutine(
                semaphore,
                self._run,
                # Args/kwargs for self._run:
                input_messages=input_messages,
                retry_callback=retry_callback,
                stream_handler=stream_handler,
                call_idx=coroutine_idx,
                **kwargs,
            )
            coroutines.append(semaphore_bounded_coroutine)

        # Await and gather coroutines
        outputs: list[Exception | InstructLmAgentOutput[LmJsonOutputModelT]]
        outputs = await asyncio.gather(*coroutines, return_exceptions=True)

        # Filter out exceptions and count the "votes"
        all_messages = []
        valid_outputs: list[InstructLmAgentOutput[LmJsonOutputModelT]] = []
        exceptions = []
        vote_counts = Counter()
        for output in outputs:
            if isinstance(output, Exception):
                exceptions.append(output)
                continue
            all_messages.append(output.messages)
            valid_outputs.append(output)
            vote = getattr(output.data, self.vote_field)
            vote_counts[vote] += 1

        # If all calls failed, raise the first exception
        if len(valid_outputs) == 0:
            self._warn("All InstructLmAgent._run calls failed. Raising first exception...")
            raise exceptions[0]

        winner = vote_counts.most_common(1)[0][0]

        # Prepare & return output
        if self.reason_field is None:
            return InstructLmAgentOutput(
                data=self.output_data_model(**{self.vote_field: winner}),
                messages=all_messages,
            )
        else:
            winning_reasons = []
            for output in valid_outputs:
                if getattr(output.data, self.vote_field) == winner:
                    winning_reasons.append(getattr(output.data, self.reason_field))
            reason_str = self.aggregate_winning_vote_reasons(
                winning_reasons=winning_reasons,
                winner=winner,
                num_winning_votes=vote_counts[winner],
                num_total_votes=self.num_calls_for_voting,
            )
            return InstructLmAgentOutput(
                data=self.output_data_model(
                    **{self.vote_field: winner, self.reason_field: reason_str}
                ),
                messages=all_messages,
            )

    async def run(
        self,
        input_messages: list[InstructLmMessage],
        retry_callback: LmRetryHandler | None = None,
        **kwargs,  # kwargs passed through to the InstructLm.generate method
    ) -> InstructLmAgentOutput[LmJsonOutputModelT]:
        """Runs the agent with the retry and voting logic specified in __init__."""
        if self.num_calls_for_voting > 1:
            return await self._run_with_voting(
                input_messages, retry_callback, self.streams_handler, **kwargs
            )
        else:
            return await self._run(
                input_messages, retry_callback, self.streams_handler, **kwargs
            )
