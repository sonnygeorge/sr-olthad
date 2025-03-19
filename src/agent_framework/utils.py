import asyncio
import functools
import inspect
import json
import logging
import re
import warnings
from collections import Counter, defaultdict
from typing import Any, Callable, List, Optional, Sequence, Type, TypeVar

from jinja2 import Template
from pydantic import BaseModel, ValidationError

from agent_framework.schema import (
    Agent,
    HasOutputData,
    InstructLmChatRole,
    InstructLmMessage,
    LmStreamsHandler,
)

BaseModelT = TypeVar("T", bound=BaseModel)


def render_single_turn_prompt_templates_and_get_messages(  # TODO: Docstring
    user_prompt_template: Template,
    user_message_input_data: Optional[BaseModel] = None,
    sys_prompt_template: Optional[Template] = None,
    sys_message_input_data: Optional[BaseModel] = None,
) -> List[InstructLmMessage]:
    # TODO: Raise error if model and template fields don't match up
    if sys_message_input_data is not None:
        sys_message_input_data = {
            k: str(v) for k, v in sys_message_input_data.__dict__.items()
        }
    else:
        sys_message_input_data = {}

    if user_message_input_data is not None:
        user_message_input_data = {
            k: str(v) for k, v in user_message_input_data.__dict__.items()
        }
    else:
        user_message_input_data = {}

    messages = []
    if sys_prompt_template is not None:
        sys_prompt = sys_prompt_template.render(**sys_message_input_data)
        messages.append(InstructLmMessage(role=InstructLmChatRole.SYS, content=sys_prompt))

    user_prompt = user_prompt_template.render(**user_message_input_data)
    messages.append(InstructLmMessage(role=InstructLmChatRole.USER, content=user_prompt))

    return messages


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


def with_retry(
    permissible_exceptions: Type[Exception] | Sequence[Type[Exception]],
    max_tries: int,
    logger: Optional[logging.Logger] = None,
):
    """Decorator that wraps a function with implicit retry logic.

    This decorator automatically handles both synchronous and asynchronous functions.
    When specified exceptions occur, it retries the function up to the maximum number
    of attempts. The final attempt will not catch exceptions, allowing them to
    propagate naturally.

    Args:
        permissible_exceptions (Type[Exception] | Sequence[Type[Exception]]): One or more
            exception classes that should trigger a retry.
        max_tries (int): Maximum number of attempts to execute the function.
        logger (Optional[logging.Logger]): Optional logger to use within the decorator.

    Returns:
        A decorated function that will retry when the specified exceptions occur.

    Example:
        >>> @with_retry(ValueError, max_tries=3)
        ... def parse_data(data):
        ...     return int(data)
    """
    T = TypeVar("T")

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def log_or_print_permissible_exception(e: Exception, tries_remaining: int) -> None:
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
                    log_or_print_permissible_exception(e, tries_remaining)
                    tries_remaining -= 1
            return func(*args, **kwargs)  # Last attempt (don't catch exceptions)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            tries_remaining = max_tries
            while tries_remaining > 1:
                try:
                    return await func(*args, **kwargs)
                except permissible_exceptions as e:
                    log_or_print_permissible_exception(e, tries_remaining)
                    tries_remaining -= 1
            return await func(*args, **kwargs)  # Last attempt (don't catch exceptions)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def identity_function(thing: Any) -> Any:
    return thing


def semaphore_bounded_call(
    semaphore: asyncio.Semaphore,
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    async def _semaphore_bounded_call():
        async with semaphore:
            return await func(*args, **kwargs)

    return _semaphore_bounded_call()


def with_implicit_async_voting(
    n_calls: int,
    max_async_calls: int,
    vote_attr: str,
    reason_attr: Optional[str] = None,
    logger: Optional[logging.Logger] = None,  # TODO: Actually use the logger?
):
    """
    Decorator that: (1) implicitly orchestrates multiple async calls to the wrapped agent,
    (2) takes a majority vote over the `getattr(AgentReturn.output_data, vote_attr)`
    attribute of the return objects, and (3) aggregates and returns a return object where:
    - `getattr(AgentReturn.output_data, vote_attr)` is the majority vote winner
    - `getattr(AgentReturn.output_data, reason_attr)` is a single string explaining that
      a vote was taken, indicating the winner, and listing the "reasons" for the winning
      vote.
    - All other `AgentReturn.output_data` attributes are aggregated `List`s of the
      respective attributes from the many calls.
    - All other `AgentReturn` attributes are aggregated `List`s of the respective
      attributes from the many calls.

    Args:
        n_calls (int): The number of times to call the agent.
        max_async_calls (int): The maximum number of asynchronous calls to make at once.
        vote_attr (str): Key for the `str` attribute in the output data that contains the
            hashable "vote" to be counted.
        reason_attr (str): Optional key for the `str` attribute in the output data
            that contains the "reason" for the vote.
        logger (Optional[logging.Logger]): Optional logger to use within the decorator.
    """
    # TODO: Type hint throughout framework or check at wrap-time that `BaseModel` fields
    # can be set to `List`s of the same type.

    if n_calls == 1:
        return identity_function

    if n_calls < 1:
        raise ValueError("n_calls_to_await must be at least 1")
    if max_async_calls < 1:
        raise ValueError("max_async_calls must be at least 1")

    def decorator(agent: Agent):
        assert inspect.iscoroutinefunction(agent.__call__) and isinstance(
            agent, Agent
        ), "Decorated function must be a coroutine (async def) `Agent`"

        @functools.wraps(agent)
        async def wrapper(*args, **kwargs):
            # Check if any LM stream handlers are present in the args or kwargs
            stream_handler_arg_idxs = []
            stream_handler_kwarg_keys = []
            for i, arg in enumerate(args):
                if isinstance(arg, LmStreamsHandler):
                    stream_handler_arg_idxs.append(i)
            for key, arg in kwargs.items():
                if isinstance(arg, LmStreamsHandler):
                    stream_handler_kwarg_keys.append(key)

            # Prepare the async calls
            semaphore = asyncio.Semaphore(max_async_calls)
            async_calls = []
            for async_call_idx in range(n_calls):
                # Bind `async_call_idx` to LM stream handlers so they can differentiate
                # between simultanous LM streams
                for idx in stream_handler_arg_idxs:
                    args[idx] = functools.partial(args[idx], stream_idx=async_call_idx)
                for key in stream_handler_kwarg_keys:
                    kwargs[key] = functools.partial(kwargs[key], stream_idx=async_call_idx)

                async_calls.append(semaphore_bounded_call(semaphore, agent, *args, **kwargs))

            # Await all async calls and gather the return objects
            return_objs: List[HasOutputData | Exception] = await asyncio.gather(
                *async_calls, return_exceptions=True
            )

            # Filter out returned exceptions and count the "votes"
            valid_returns: List[HasOutputData] = []
            exceptions = []
            vote_counter = Counter()
            for return_obj in return_objs:
                if isinstance(return_obj, Exception):
                    exceptions.append(return_obj)
                    continue
                valid_returns.append(return_obj)
                vote = getattr(return_obj.output_data, vote_attr)
                vote_counter[vote] += 1

            if len(valid_returns) == 0:
                warning = "All invoked agent calls failed. Returning first exception."
                warnings.warn(warning)
                raise exceptions[0]

            # Prepare return object
            voted_class = vote_counter.most_common(1)[0][0]
            aggregated_output_data = defaultdict(list)
            aggregated_return_object = defaultdict(list)
            winning_vote_reasons = []

            for return_obj in valid_returns:
                # Aggregate return object attributes into lists
                for attr_k, attr_v in return_obj.__dict__.items():
                    if attr_k != "output_data":
                        aggregated_return_object[attr_k].append(attr_v)

                # Aggregate vote reasons into a list that will be stringified later
                vote = getattr(return_obj.output_data, vote_attr)
                if vote == voted_class and reason_attr is not None:
                    assert hasattr(return_obj.output_data, reason_attr), (
                        "Wrapped agent did not return an output data object with "
                        f"vote reason string attribute '{reason_attr}' "
                    )
                    winning_vote_reasons.append(getattr(return_obj.output_data, reason_attr))

                # Aggregate other output data attributes into lists
                for attr_k, attr_v in return_obj.output_data.__dict__.items():
                    if attr_k != vote_attr and attr_k != reason_attr:
                        aggregated_output_data[attr_k].append(attr_v)

            # Stringify the list of winning vote reasons
            aggregated_output_data[vote_attr] = voted_class
            if reason_attr is not None:
                reason_str = (  # TODO: Make this fstring template a default argument
                    f"'{voted_class}' was chosen since, in a multi-agent vote, it"
                    f" received {vote_counter[voted_class]}/{n_calls} votes"
                    f" for the following reasons:\n{winning_vote_reasons}"
                )  # TODO: Add this fstring template to sr-OLTHAD config
                aggregated_output_data[reason_attr] = reason_str

            # Finalize and return the aggregated return object
            return valid_returns[0].__class__(
                output_data=valid_returns[0].output_data.__class__(**aggregated_output_data),
                **aggregated_return_object,
            )

        return wrapper

    return decorator
