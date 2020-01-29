from enum import Enum


class Intent(int, Enum):
    location = 1
    route = 2
    action = 3
    config = 4
    others = 5


LOCATION_REGEX = ['ở đâu', 'chỗ nào']
ROUTE_REGEX = ['chỉ đường']
ACTION_REGEX = ['bật', 'tắt', 'mở', 'đóng', 'giảm', 'tăng']
