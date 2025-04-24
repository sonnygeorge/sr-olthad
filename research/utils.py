import re


def to_lower_snake_case(s: str) -> str:
    # Replace non-alphanumeric characters with spaces
    cleaned: str = re.sub(r"[^a-zA-Z0-9]", " ", s)
    # Extract words from the cleaned string
    words: list[str] = re.findall(r"[a-zA-Z0-9]+", cleaned)
    # Convert all words to lowercase and join with underscores
    return "_".join(word.lower() for word in words)


def is_function_call(s: str) -> bool:
    """
    Check if a string represents a valid function call using regex.
    Returns True if the string matches a function call pattern, False otherwise.

    Examples:
        "foo()" -> True
        "bar(fizz='buzz')" -> True
        "someFunction([10, 10, 10], 'arg')" -> True
        "not_a_function" -> False
        "123()" -> False
    """
    # Strip leading and trailing whitespace
    s = s.strip()

    # Regex pattern explanation:
    # ^[a-zA-Z_][a-zA-Z0-9_]* - Starts with a valid function name (letters or underscore, followed by letters, numbers, or underscore)
    # \s* - Optional whitespace before parentheses
    # \( - Opening parenthesis
    # (?:[^()]+|\([^()]*\))* - Non-capturing group for arguments: matches content that's not parentheses or balanced nested parentheses
    # \) - Closing parenthesis
    # \s*$ - Optional trailing whitespace at end
    pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*\s*\((?:[^()]+|\([^()]*\))*\)\s*$"

    return bool(re.match(pattern, s))


# Test cases
if __name__ == "__main__":
    test_cases = [
        "foo()",  # Simple no args
        " bar( ) ",  # Whitespace
        "bar(fizz='buzz')",  # Keyword arg
        "someFunction([10, 10, 10], 'arg')",  # List and string args
        "nested(func())",  # Nested function call
        "x_y_z(123)",  # Underscores in name
        "not_a_function",  # No parentheses
        "123()",  # Invalid name (starts with number)
        "func(arg",  # Unclosed parenthesis
        "func())",  # Unbalanced parentheses
        "",  # Empty string
    ]

    for test in test_cases:
        print(f"'{test}' -> {is_function_call(test)}")
