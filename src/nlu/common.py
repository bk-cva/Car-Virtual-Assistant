import os.path

MODEL_DIR = '/models'

PHONE_CALL_REGEX = [
    r'^gọi điện thoại cho (?P<person_name>[\w\s]+)',
    r'^gọi điện thoại tới (?P<person_name>[\w\s]+)',
    r'^gọi điện cho (?P<person_name>[\w\s]+)',
    r'^gọi điện tới (?P<person_name>[\w\s]+)',
    r'^gọi cho (?P<person_name>[\w\s]+)',
    r'^gọi tới (?P<person_name>[\w\s]+)',
    r'^gọi (?P<person_name>[\w\s]+)',
]

PHONE_TEXT_REGEX = [
    r'^nhắn tin cho (?P<person_name>[\w\s]+) rằng (?P<message>[\w\s]+)',
    r'^nhắn cho (?P<person_name>[\w\s]+) rằng (?P<message>[\w\s]+)',
    r'^nhắn (?P<person_name>[\w\s]+) rằng (?P<message>[\w\s]+)',
]

SELECT_ITEM_REGEX = [
    r'cái thứ (?P<number>\w+)$',
    r'cái số (?P<number>\w+)$',
    r'cái (?P<number>đầu tiên)',
]

NORMALIZE_ENTITY_DICT = {
    'number': {
        1: ['nhất', 'đầu tiên', 'một'],
        2: ['hai', 'nhì'],
        3: ['ba'],
        4: ['bốn', 'tư'],
        5: ['năm'],
    }
}
