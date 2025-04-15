from typing import ClassVar

from pydantic import BaseModel, Field

from sr_olthad.framework.utils import get_prompt_json_spec


class TestGetPromptJsonSpec:
    class DummyBaseModel(BaseModel):
        answer_attr: ClassVar[str] = "answer"
        retrospective_attr: ClassVar[str] = "retrospective"

        # Fields
        answer: str = Field(
            description="Your answer choice.",
            json_schema_extra={"field_type": "str"},
        )
        retrospective: str = Field(
            description="A short retrospective.",
            json_schema_extra={"field_type": "str"},
        )

    def test_output_is_as_expected(self):
        expected = '{\n  "answer": "(str) Your answer choice.",\n  "retrospective": "(str) A short retrospective."\n}'
        assert get_prompt_json_spec(TestGetPromptJsonSpec.DummyBaseModel) == expected


if __name__ == "__main__":
    test = TestGetPromptJsonSpec()
    test.test_output_is_as_expected()
