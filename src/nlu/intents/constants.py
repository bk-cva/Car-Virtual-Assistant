from enum import Enum


class Intent(int, Enum):
    path = 0
    location = 1
    music = 2
    remind = 3
    control_door = 4
    control_window = 5
    control_aircon = 6
    control_radio = 7
    schedule = 8
    request_news = 9
    phone_call = 1000
    phone_text = 1001


PHONE_CALL_REGEX = [
    '^gọi',
]
PHONE_TEXT_REGEX = [
    '^nhắn',
    '^gửi tin',
]
