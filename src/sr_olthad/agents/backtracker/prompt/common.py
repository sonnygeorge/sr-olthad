from enum import StrEnum

from pydantic import BaseModel


class BacktrackerSubAgentPromptInputData(BaseModel):
    """Data to be rendered in the user prompt for the Backtracker sub-agents.

    Attributes:
        env_state (str): PRE-STRINGIFIED current environment state.
        olthad (str): PRE-STRINGIFIED root task node of the OLTHAD being traversed.
        task_in_question (str): PRE-STRINGIFIED task node we're considering backtracking
            from.
    """

    env_state: str
    olthad: str
    task_in_question: str


class BacktrackerSubAgentInputFields(StrEnum):
    ENV_STATE = "env_state"
    OLTHAD = "olthad"
    TASK_IN_QUESTION = "task_in_question"


class BacktrackerSubAgentLmResponseOutputData(BaseModel):
    """
    Output-JSON data to be parsed from the LM's response used by Backtracker sub-agents.

    Attributes:
        answer (str): The answer choice made by the LM.
        retrospective (str): Brief reasoning behind the answer choice.
    """

    answer: str
    retrospective: str | None


class BacktrackerSubAgentOutputFields(StrEnum):
    ANSWER = "answer"
    RETROSPECTIVE = "retrospective"


JSON_FORMAT_SYS_PROMPT_INSERT = f"""{{
    "{BacktrackerSubAgentOutputFields.ANSWER}": "(str) Your answer choice",
    "{BacktrackerSubAgentOutputFields.RETROSPECTIVE}": "(str) A BRIEF summary of your earlier reasoning",
}}"""
