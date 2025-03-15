from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


class BacktrackerSubAgentInputPromptData(BaseModel):
    """Data to be rendered in the user prompt for the Backtracker sub-agents.

    Attributes:
        env_state (str): PRE-STRINGIFIED current environment state.
        olthad (str): PRE-STRINGIFIED root node of the OLTHAD being traversed.
        task_in_question (str): PRE-STRINGIFIED node we're considering backtracking from.
    """

    env_state: str
    olthad: str
    task_in_question: str


class BacktrackerSubAgentInputFields(StrEnum):
    ENV_STATE = "env_state"
    OLTHAD = "olthad"
    TASK_IN_QUESTION = "task_in_question"


class BacktrackerSubAgentOutputPromptData(BaseModel):
    """
    Output-JSON data to be parsed from the LM's response used by Backtracker sub-agents.
    """

    answer: str
    retrospective: Optional[str]


class BacktrackerSubAgentOutputFields(StrEnum):
    ANSWER = "answer"
    RETROSPECTIVE = "retrospective"


JSON_FORMAT_SYS_PROMPT_INSERT = f"""{{
    "{BacktrackerSubAgentOutputFields.ANSWER}": "(str) Your answer choice",
    "{BacktrackerSubAgentOutputFields.RETROSPECTIVE}": "(str) A BRIEF summary of your earlier reasoning",
}}"""
