from enum import Enum


class SPEED(Enum):
    LOW = 3
    MEDIUM = 2
    HIGH = 1


class MSG_TYPE(Enum):
    CLIENT = 1
    PREPARE = 2
    PROMISE = 3
    ACCEPT = 4
    ACCEPTED = 5
    DECIDE = 6
    DENIED = 7
    REPL = 8
    ASKFORLOG = 10
    MISSINGLOG = 11
