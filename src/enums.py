from enum import StrEnum


class SerializationMethod(StrEnum):
    JSON = "json"
    YAML = "yaml"


class InstructLmChatRole(StrEnum):
    SYS = "system"
    USER = "user"
    ASSISTANT = "assistant"
