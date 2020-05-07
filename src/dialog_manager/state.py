from enum import Enum


class State(int, Enum):
    START = 0
    LOCATION = 1
    FIND_LOCATION = 2
    FIND_ADDRESS = 3
    FIND_CURRENT = 4
    NO_LOCATION = 5
    SELECT_LOCATION = 6
    RETURN_LOCATION = 7
    CREATE_SCHEDULE = 8
    ASK_EVENT = 9
    ASK_TIME = 10
    ASK_DATE = 11
    CREATING_SCHEDULE = 12
