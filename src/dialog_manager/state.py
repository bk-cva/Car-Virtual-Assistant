from enum import Enum


class State(int, Enum):
    START = 0
    END = 1
    FIND_LOCATION = 2
    SELECT_LOCATION = 3
    FIND_PATH = 4
