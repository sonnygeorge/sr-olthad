from enum import StrEnum


class SerializationMethod(StrEnum):
    JSON = "json"
    YAML = "yaml"


class InstructLmChatRole(StrEnum):
    SYS = "system"
    USER = "user"
    ASSISTANT = "assistant"


class BinaryCaseStr(StrEnum):
    TRUE = "true"
    FALSE = "false"
