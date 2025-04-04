import asyncio
import inspect
import json
import re
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any, TypeVar

from jinja2 import Template
from pydantic import BaseModel, ValidationError
from typing_extensions import ParamSpec

from common.schema import (
    InstructLmChatRole,
    InstructLmMessage,
)

BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


def get_prompt_json_spec(model_class: type[BaseModel]) -> str:
    """
    Given a Pydantic BaseModel type, returns a string to communicate the specifications of
    a JSON (e.g., that it should output).
    """
    schema = model_class.model_json_schema()
    schema_properties: dict[str, dict[str, Any]] = schema.get("properties", {})
    result = {}
    for field_name, field_props in schema_properties.items():
        field_type = field_props.get("field_type", "Any?")
        description = field_props.get("description", f"The {field_name}.")
        result[field_name] = f"({field_type}) {description}"
    return json.dumps(result)


def render_single_turn_prompt_templates_and_get_messages(
    user_prompt_template: Template,
    user_prompt_input_data: BaseModel | None = None,
    sys_prompt_template: Template | None = None,
    sys_prompt_input_data: BaseModel | None = None,
) -> list[InstructLmMessage]:
    """Renders pydantic data model instances into single-turn prompt templates"""
    # TODO: Raise error if model and template fields don't match up
    if sys_prompt_input_data is not None:
        sys_prompt_input_data = {
            k: str(v) for k, v in sys_prompt_input_data.__dict__.items()
        }
    else:
        sys_prompt_input_data = {}

    if user_prompt_input_data is not None:
        user_prompt_input_data = {
            k: str(v) for k, v in user_prompt_input_data.__dict__.items()
        }
    else:
        user_prompt_input_data = {}

    messages = []
    if sys_prompt_template is not None:
        sys_prompt = sys_prompt_template.render(**sys_prompt_input_data)
        messages.append(InstructLmMessage(role=InstructLmChatRole.SYS, content=sys_prompt))

    user_prompt = user_prompt_template.render(**user_prompt_input_data)
    messages.append(InstructLmMessage(role=InstructLmChatRole.USER, content=user_prompt))

    return messages


def detect_extract_and_parse_json_from_text(
    text: str, model_to_extract: type[BaseModelT]
) -> BaseModelT:
    """
    Detects, extracts, and parses JSON from text as a specified Pydantic BaseModel.

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
                ) from e
        raise ValueError("No valid JSON could be parsed from the text")
    except Exception as e:
        raise ValueError(f"Error processing text: {str(e)}") from e


P = ParamSpec("P")
T = TypeVar("T")


def get_semaphore_bound_coroutine(
    semaphore: asyncio.Semaphore,
    func: Callable[P, Awaitable[T]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> Coroutine[Any, Any, T]:
    async def _semaphore_bound_coroutine() -> T:
        async with semaphore:
            return await func(*args, **kwargs)

    return _semaphore_bound_coroutine()


async def call_or_await(fn: Callable[P, Any], *args: P.args, **kwargs: P.kwargs):
    if inspect.iscoroutinefunction(fn) or inspect.isasyncgenfunction(fn):
        return await fn(*args, **kwargs)
    return fn(*args, **kwargs)
