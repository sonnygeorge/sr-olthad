from sr_olthad.prompts.backtracker.exhaustive_effort_clf import EFFORT_WAS_EXHAUSTIVE_OPTIONS
from sr_olthad.utils import extract_letter_from_multiple_choice_response


class TestExtractLetterFromMultipleChoiceResponse:
    def test_output_is_letter_when_answer_contains_letter_and_text(self):
        # TODO: Technically, this is an integration test. So, we would, in theory, want to
        # remove the dependency on the details of EFFORT_WAS_EXHAUSTIVE_OPTIONS.
        ans = "B. No, there are still reasonable things that could be done to accomplish the task."
        opts = EFFORT_WAS_EXHAUSTIVE_OPTIONS
        assert extract_letter_from_multiple_choice_response(ans, opts) == opts[False].letter
        ans = "B. No, there are still things to do."
        opts = EFFORT_WAS_EXHAUSTIVE_OPTIONS
        assert extract_letter_from_multiple_choice_response(ans, opts) == opts[False].letter


if __name__ == "__main__":
    test = TestExtractLetterFromMultipleChoiceResponse()
    test.test_output_is_letter_when_answer_contains_letter_and_text()
