import re
from datetime import date, timedelta, datetime, time
from typing import Tuple

from src.proto.rest_api_pb2 import Entity
from src.nlu.intents.constants import Intent


NORMALIZE_ENTITY_DICT = {
    'number': {
        0: ['1', 'nhất', 'đầu tiên', 'một'],
        1: ['2', 'hai', 'nhì'],
        2: ['3', 'ba'],
        3: ['4', 'bốn', 'tư'],
        4: ['5', 'năm'],
        5: ['6', 'sáu'],
        6: ['7', 'bảy'],
        7: ['8', 'tám'],
        8: ['9', 'chín'],
        9: ['10', 'mười'],
    },
    'info_type': {
        'khoảng cách': ['bao xa', 'xa'],
        'thời gian': ['bao lâu', 'lâu'],
    },
    'place_property': {
        'gần nhất': ['gần nhất', 'gần đây nhất', 'xung quanh', 'gần đây']
    }
}

DATE_DICT = {
    0: ['nay', 'hôm nay', 'ngày hôm nay'],
    1: ['mai', 'ngày mai', 'hôm sau', 'ngày hôm sau'],
    2: ['mốt', 'ngày mốt'],
}

weekday = {
    'hai': 2,
    'ba': 3,
    'tư': 4,
    'năm': 5,
    'sáu': 6,
    'bảy': 7,
    'chủ nhật': 8,
}

OFFSET_TIME = 10 % 30

TYPE_SPACE_LIST = ['kém', 'hơn', 'đúng', 'rưỡi']
PERIOD_LIST = ['sáng', 'trưa', 'chiều', 'tối', 'khuya', 'đêm']


class NormalizationError(Exception):
    pass


class NormalEntity:
    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value


def normalize_date(entity: str) -> date:
    for normalized_value, possible_values in DATE_DICT.items():
        if entity in possible_values:
            entity = normalized_value
    date_value = entity
    if isinstance(date_value, int):
        return date.today() + timedelta(date_value)

    match_weekday = re.match(r'(thứ (?P<d>\w+))|(?P<c>chủ nhật)', date_value)
    match_date = re.match(r'ngày (?P<d>\d+)', date_value)
    if match_weekday:
        if match_weekday.group('d'):
            date_value = match_weekday.group('d')
        else:
            date_value = match_weekday.group('c')
        if date_value.isdecimal():
            date_value = int(date_value)
            if date_value < 2 or date_value > 7:
                raise NormalizationError('Invalid date value {}'.format(date_value))
        else:
            if date_value in weekday:
                date_value = weekday[date_value]
            else:
                raise NormalizationError('Invalid date value {}'.format(date_value))
        today = date.today()
        days_ahead = date_value - 1 - today.isoweekday()
        if days_ahead < 0:
            days_ahead += 7
        return today + timedelta(days_ahead)

    if match_date:
        date_value = int(match_date.group('d'))
        today = date.today()
        days_ahead = date_value - today.day
        if days_ahead < 0:
            # set the desired day is that day in the next month as default
            return today.replace(month=(today.month)%12+1, day=date_value)
        return date(today.year, today.month, date_value)

    raise NormalizationError('Unknown date value: {}'.format(entity))


def normalize_time_range(entity: str) -> Tuple[time, time]:
    time_value = re.sub(r'giờ\s?', '', entity.lower())
    # full: ex. '5 giờ kém chiều'
    full_time = re.match(r'(?P<t>\d+) (?P<a>\D+) (?P<p>\D+)', time_value)
    # period: ex. '5 giờ chiều', '5 giờ kém'
    after_time = re.match(r'(?P<t>\d+) (?P<v>\w+)', time_value)
    # only period: ex. 'chiều', 'sáng'
    period_time = re.match(r'(?P<p>\D+)', time_value)
    # full: ex. '15:30 chiều'
    full_oclock_time = re.match(r'((?P<h1>\d+):(?P<m>\d+))|(?P<h2>\d+) (?P<p>\w+)', time_value)
    # oclock: ex. '15:30'
    oclock_time = re.match(r'((?P<h1>\d+):(?P<m>\d+))|(?P<h2>\d+)', time_value)
    def time_to_time_space(hours, mins=0, type_space=None):
        if type_space == 'rưỡi':
            start_time = time(hours, 30)
            end_time = time(hours, 30 + OFFSET_TIME)
        elif type_space == 'kém':
            start_time = time(hours - 1, 30)
            end_time = time(hours)
        elif type_space == 'hơn':
            start_time = time(hours)
            end_time = time(hours, 30)
        else:
            start_time = time(hours, mins)
            end_time = time(hours, mins + OFFSET_TIME)

        return (start_time, end_time)

    if full_time:
        clock = int(full_time.group('t'))
        type_space = full_time.group('a')
        period = full_time.group('p')
        if clock > 12:
            return time_to_time_space(clock, type_space=type_space)
        if period == 'sáng' or (period == 'trưa' and clock >= 10):
            return time_to_time_space(clock, type_space=type_space)
        return time_to_time_space((clock + 12)%24, type_space=type_space)

    elif after_time:
        clock = int(after_time.group('t'))
        enhenced_info = after_time.group('v')
        if enhenced_info in TYPE_SPACE_LIST:
            start_time, end_time = time_to_time_space(clock, type_space=enhenced_info)
            current_time = datetime.now().time()
            if start_time < current_time and (clock < 12):
                start_time = (datetime.combine(date.today(), start_time) + timedelta(hours=12)).time()
                end_time = (datetime.combine(date.today(), end_time) + timedelta(hours=12)).time()
            return (start_time, end_time)
        if enhenced_info in PERIOD_LIST:
            if clock > 12:
                return time_to_time_space(clock)
            if enhenced_info == 'sáng' or (enhenced_info == 'trưa' and clock >= 10):
                return time_to_time_space(clock)
            return time_to_time_space((clock + 12)%24)

    elif period_time:
        period = period_time.group('p')
        if period == 'sáng':
            start_time = time(3)
            end_time = time(11)
        elif period == 'trưa':
            start_time = time(11)
            end_time = time(13)
        elif period == 'chiều':
            start_time = time(13)
            end_time = time(18)
        elif period == 'khuya':
            start_time = time(0)
            end_time = time(3)
        else:
            start_time = time(0)
            end_time = time(12)
        return (start_time, end_time)

    elif full_oclock_time:
        if full_oclock_time.group('h1'):
            hours = int(full_oclock_time.group('h1'))
            mins = int(full_oclock_time.group('m'))
        else:
            hours = int(full_oclock_time.group('h2'))
            mins = 0
        period = full_oclock_time.group('p')
        if hours > 12:
            return time_to_time_space(hours=hours, mins=mins)
        if period == 'sáng' or (period == 'trưa' and hours >= 10):
            return time_to_time_space(hours=hours, mins=mins)
        return time_to_time_space(hours=(hours + 12)%24, mins=mins)

    elif oclock_time:
        if oclock_time.group('h1'):
            hours = int(oclock_time.group('h1'))
            mins = int(oclock_time.group('m'))
        else:
            hours = int(oclock_time.group('h2'))
            mins = 0
        start_time, end_time = time_to_time_space(hours=hours, mins=mins)
        current_time = datetime.now().time()
        if start_time < current_time and (hours < 12):
            start_time = (datetime.combine(date.today(), start_time) + timedelta(hours=12)).time()
            end_time = (datetime.combine(date.today(), end_time) + timedelta(hours=12)).time()
        return (start_time, end_time)

    raise NormalizationError('Unknown time value: {}'.format(entity))


def normalize_time(entity: str) -> time:
    time_value = re.sub(r'giờ\s?', '', entity.lower())
    # oclock: ex. '15:30'
    oclock_time = re.match(r'((?P<h1>\d+):(?P<m>\d+))|(?P<h2>\d+)', time_value)

    if oclock_time:
        if oclock_time.group('h1'):
            hours = int(oclock_time.group('h1'))
            mins = int(oclock_time.group('m'))
        else:
            hours = int(oclock_time.group('h2'))
            mins = 0
        start_time = time(hours, mins)
        current_time = datetime.now().time()
        if start_time < current_time and (hours < 12):
            start_time = (datetime.combine(date.today(), start_time) + timedelta(hours=12)).time()
        return start_time

    raise NormalizationError('Unknown time value: {}'.format(entity))


def normalize_duration(entity: str) -> time:
    time_value = re.sub(r'giờ\s?', '', entity.lower())
    # oclock: ex. '15:30'
    oclock_time = re.match(r'((?P<h1>\d+):(?P<m>\d+))|(?P<h2>\d+)', time_value)

    if oclock_time:
        mins = 0
        if oclock_time.group('h1'):
            hours = int(oclock_time.group('h1'))
            mins = int(oclock_time.group('m'))
        else:
            hours = int(oclock_time.group('h2'))
        return time(hours, mins)

    raise NormalizationError('Unknown time value: {}'.format(entity))


def normalize(intent: Intent, entity: Entity) -> NormalEntity:
    result = NormalEntity(entity.name, entity.value)
    if result.name in NORMALIZE_ENTITY_DICT:
        for normalized_value, possible_values in NORMALIZE_ENTITY_DICT[result.name].items():
            if result.value in possible_values:
                result.value = normalized_value
    return result
