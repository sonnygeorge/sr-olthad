from enum import StrEnum


class SerializationMethod(StrEnum):
    JSON = "json"
    YAML = "yaml"


class InstructLmChatRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
