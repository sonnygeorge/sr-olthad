import inspect

from sr_olthad.schema import BinaryChoiceOptions, NonBinaryChoiceOptions


def extract_letter_from_multiple_choice_question_response(
    text: str,
    options: BinaryChoiceOptions | NonBinaryChoiceOptions,
) -> str:
    for option in options.values():
        option_letter_clean = "".join(c for c in option.letter if c.isalpha()).lower()
        option_text_clean = "".join(c for c in option.text if c.isalpha()).lower()
        chosen_clean = "".join(c for c in text if c.isalpha()).lower()
        if option_letter_clean == chosen_clean:
            return option.letter
        if option_text_clean in chosen_clean:
            return option.letter
    # TODO: Fuzzy matching? (possibly... certainly not urgent)
    raise ValueError("None of the answer choices were found in the text")


async def call_or_await(handler, *args, **kwargs):
    if inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler):
        return await handler(*args, **kwargs)
    return handler(*args, **kwargs)
