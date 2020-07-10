from .intent import Intent

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

YES_REGEX = [
    r'^có$',
    r'^ok$',
    r'^ừ$',
    r'^ừm$',
]

NO_REGEX = [
    r'^không$',
]

regex_list = [
    (PHONE_CALL_REGEX, Intent.phone_call),
    (PHONE_TEXT_REGEX, Intent.phone_text),
    (YES_REGEX, Intent.yes),
    (NO_REGEX, Intent.no),
]
