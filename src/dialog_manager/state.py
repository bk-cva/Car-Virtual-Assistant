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
    POST_RETURN_LOCATION = 9
    ROUTE = 10
    ASK_PLACE = 11
    FIND_ROUTE = 12
    REQUEST_SCHEDULE = 13
    CREATE_SCHEDULE = 14
    ASK_EVENT = 15
    ASK_TIME = 16
    ASK_DURATION = 17
    CALL_CREATE_SCHEDULE = 18
    CANCEL_SCHEDULE = 19
    NO_SCHEDULE = 20
    SELECT_SCHEDULE = 21
    ASK_CANCEL = 22
    CALL_CANCEL_SCHEDULE = 23
    ABORT_CANCEL = 24
