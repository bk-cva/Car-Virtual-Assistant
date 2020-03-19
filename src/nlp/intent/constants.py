from enum import Enum


class Intent(int, Enum):
    path = 0
    location = 1
    music = 2
    remind = 3
    control_door = 4
    control_window = 5


LOCATION_REGEX = ['ở đâu', 'chỗ nào']
ROUTE_REGEX = ['chỉ đường', 'đưa tôi', 'cho tôi tới']
ACTION_REGEX = ['bật', 'tắt', 'mở', 'đóng', 'giảm', 'tăng']
