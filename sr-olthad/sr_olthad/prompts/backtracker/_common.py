from typing import ClassVar

from pydantic import BaseModel, Field


class BacktrackerSubAgentLmResponseOutputData(BaseModel):
    # NOTE: These must correspond to the field attrs below.
    answer_attr: ClassVar[str] = "answer"
    retrospective_attr: ClassVar[str] = "retrospective"

    # Fields
    answer: str = Field(
        description="Your answer choice.",
        json_schema_extra={"field_type": "str"},
    )
    retrospective: str = Field(
        description="A short retrospective that could be added to the OLTHAD.",
        json_schema_extra={"field_type": "str"},
    )
