from enum import Enum


class State(int, Enum):
    START = 0
    LOCATION = 1
    FIND_LOCATION = 2
    FIND_ADDRESS = 3
    FIND_CURRENT = 4
    NO_LOCATION = 5
    AUTO_SELECT = 6
    SELECT_LOCATION = 7
    RETURN_LOCATION = 8
    CREATE_SCHEDULE = 9
    ASK_EVENT = 10
    ASK_TIME = 11
    ASK_DATE = 12
    CREATING_SCHEDULE = 13
