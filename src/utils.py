import asyncio
import json
import warnings
import yaml
from collections import Counter
from typing import List, Literal

from types_and_models import (
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
        serialization_method: Literal["json", "yaml"] = "json",
        indent: int = 2,
    ) -> str:
        if serialization_method == "json":
            return cls._json_stringify(data, indent)
        elif serialization_method == "yaml":
            return cls._yaml_stringify(data, indent)
        else:
            raise ValueError("Invalid serialization method")


def implicitly_call_multiple_times_and_take_majority_vote(
    num_calls: int = 3, max_async_calls: int = 30
):
    """
    Decorator to wrap `MultipleChoiceQuestionAgent.__call__` implicitly invokes and
    asynchronously awaits multiple calls to the decorated method, ultimately returning
    a `MultipleChoiceQuestionAgentOutputData` object with the `chosen` answer being
    the most common answer choice among the outputs and the `reasoning` string being
    a summary of the votes.
    """
    if num_calls < 1:
        raise ValueError("n_calls_to_await must be at least 1")
    if max_async_calls < 1:
        raise ValueError("max_async_calls must be at least 1")

    def decorator(agent_callable: MultipleChoiceQuestionAgent):
        async def method_wrapper(self: MultipleChoiceQuestionAgent, *args, **kwargs):
            # Invoke the decorated method multiple times asynchronously
            semaphore = asyncio.Semaphore(max_async_calls)

            async def bounded_call():
                async with semaphore:
                    return await agent_callable(self, *args, **kwargs)

            async_tasks = [bounded_call() for _ in range(num_calls)]
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
                f" received {counter[voted_answer_choice]}/{num_calls} votes"
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
