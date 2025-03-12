import asyncio
import functools
import json
import logging
import inspect
import re
import warnings
import yaml
from collections import Counter
from typing import Callable, Type, Union, List, Tuple, Optional, Any, TypeVar

from pydantic import BaseModel, ValidationError

from enums import SerializationMethod
from schema import (
    JsonSerializable,
    MultipleChoiceQuestionAgent,
    MultipleChoiceQuestionAgentOutputData,
    MultipleChoiceQuestionAgentReturn,
)


class StructuredDataStringifier:
    @classmethod
    def _json_stringify(cls, data: JsonSerializable, indent: int) -> str:
        return json.dumps(data, indent=indent)

    @classmethod
    def _yaml_stringify(cls, data: JsonSerializable, indent: int) -> str:
        return yaml.dump(data, indent=indent, sort_keys=False)

    @classmethod
    def stringify(
        cls,
        data: JsonSerializable,
        serialization_method: SerializationMethod = SerializationMethod.YAML,
        indent: int = 2,
    ) -> str:
        if serialization_method == SerializationMethod.JSON:
            return cls._json_stringify(data, indent)
        elif serialization_method == SerializationMethod.YAML:
            return cls._yaml_stringify(data, indent)
        else:
            raise ValueError("Invalid serialization method")


BaseModelT = TypeVar("T", bound=BaseModel)


def detect_extract_and_parse_json_from_text(
    text: str, model_to_extract: Type[BaseModelT]
) -> BaseModelT:
    """
    Detects, extracts, and parses JSON from text into a specified Pydantic BaseModel.

    Raises:
        ValueError: If no valid JSON is found in the text
        ValidationError: If the JSON doesn't match the model's structure
    """
    try:
        # Pattern to match JSON objects (including nested) between curly braces
        json_pattern = r"\{(?:[^{}]|\{[^{}]*\})*\}"
        matches = re.findall(json_pattern, text)
        if not matches:
            raise ValueError("No valid JSON found in the text")
        for match in matches:
            try:
                json_data = json.loads(match)
                return model_to_extract(**json_data)
            except json.JSONDecodeError:
                continue  # Silently try next match if JSON parsing fails
            except ValidationError as e:
                raise ValidationError(
                    f"JSON data doesn't match the expected model structure: {str(e)}",
                    model_to_extract,
                )
        raise ValueError("No valid JSON could be parsed from the text")
    except Exception as e:
        raise ValueError(f"Error processing text: {str(e)}")


def implicitly_call_multiple_times_and_take_majority_vote(
    n_calls: int = 3, max_async_calls: int = 30
):
    """
    Decorator to wrap `MultipleChoiceQuestionAgent.__call__` implicitly invokes and
    asynchronously awaits multiple calls to the decorated method, ultimately returning
    a `MultipleChoiceQuestionAgentOutputData` object with the `chosen` answer being
    the most common answer choice among the outputs and the `reasoning` string being
    a summary of the votes.
    """
    if n_calls < 1:
        raise ValueError("n_calls_to_await must be at least 1")
    if max_async_calls < 1:
        raise ValueError("max_async_calls must be at least 1")

    # If num_calls is 1, just return the function as-is without wrapping
    def identity_decorator(agent_callable: MultipleChoiceQuestionAgent):
        return agent_callable

    if n_calls == 1:
        return identity_decorator

    def decorator(agent_callable: MultipleChoiceQuestionAgent):
        async def method_wrapper(self: MultipleChoiceQuestionAgent, *args, **kwargs):
            # Invoke the decorated method multiple times asynchronously
            semaphore = asyncio.Semaphore(max_async_calls)

            async def bounded_call():
                async with semaphore:
                    return await agent_callable(self, *args, **kwargs)

            async_tasks = [bounded_call() for _ in range(n_calls)]
            return_objs: List[MultipleChoiceQuestionAgentReturn] = await asyncio.gather(
                *async_tasks, return_exceptions=True
            )

            # Filter out exceptions and count the votes
            valid_return_objs: List[MultipleChoiceQuestionAgentReturn] = []
            exceptions = []
            counter = Counter()
            for return_obj in return_objs:
                if isinstance(return_obj, Exception):
                    exceptions.append(return_obj)
                    continue
                valid_return_objs.append(return_obj)
                counter[return_obj.output_data.chosen] += 1

            if len(valid_return_objs) == 0:
                warning = "All invoked agent calls failed. Returning first exception."
                warnings.warn(warning)
                raise exceptions[0]

            # Prepare aggregate return object and return
            voted_answer_choice = counter.most_common(1)[0][0]
            reasons_for_winning_vote = []
            convos = []
            for return_obj in valid_return_objs:
                convos.append(return_obj.messages)
                if return_obj.output_data.chosen == voted_answer_choice:
                    reasons_for_winning_vote.append(return_obj.output_data.reasoning)
            winning_votes_str = StructuredDataStringifier.stringify(
                reasons_for_winning_vote, serialization_method="yaml"
            )
            reasoning = (
                f"'{voted_answer_choice}' was chosen since, in a multi-agent vote, it"
                f" received {counter[voted_answer_choice]}/{n_calls} votes"
                f" for the following reasons:\n{winning_votes_str}"
            )
            output_data = MultipleChoiceQuestionAgentOutputData(
                chosen=voted_answer_choice, reasoning=reasoning
            )
            return MultipleChoiceQuestionAgentReturn(
                output_data=output_data, messages=convos
            )

        return method_wrapper

    return decorator


def with_retry(
    permissible_exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]],
    max_tries: int = 3,
    logger: Optional[logging.Logger] = None,
):
    T = TypeVar("T")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def log_or_print_exception(e: Exception, tries_remaining: int) -> None:
            msg = f"Retrying {func.__name__}: {str(e)}, {tries_remaining-1} tries remaining"
            if logger:
                logger.warning(msg)
            else:
                print(msg)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            tries_remaining = max_tries
            while tries_remaining > 1:
                try:
                    return func(*args, **kwargs)
                except permissible_exceptions as e:
                    log_or_print_exception(e, tries_remaining)
                    tries_remaining -= 1
            return func(*args, **kwargs)  # Last attempt (don't catch exceptions)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            tries_remaining = max_tries
            while tries_remaining > 1:
                try:
                    return await func(*args, **kwargs)
                except permissible_exceptions as e:
                    log_or_print_exception(e, tries_remaining)
                    tries_remaining -= 1
            return await func(*args, **kwargs)  # Last attempt (don't catch exceptions)

        # Check if the function is a coroutine function (async def)
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
