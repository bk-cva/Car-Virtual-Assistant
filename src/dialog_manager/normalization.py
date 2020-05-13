import re
from datetime import date, timedelta, datetime

from src.proto.rest_api_pb2 import Entity


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
    'date': {
        0: ['nay', 'hôm nay', 'ngày hôm nay'],
        1: ['mai', 'ngày mai', 'hôm sau', 'ngày hôm sau'],
        2: ['mốt', 'ngày mốt'],
    }
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


class NormalizationError(Exception):
    pass


class NormalEntity:
    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value


def normalize(entity: Entity) -> NormalEntity:
    result = NormalEntity(entity.name, entity.value)
    if result.name in NORMALIZE_ENTITY_DICT:
        for normalized_value, possible_values in NORMALIZE_ENTITY_DICT[result.name].items():
            if result.value in possible_values:
                result.value = normalized_value

    if result.name == 'date':
        date_value = result.value
        if isinstance(date_value, int):
            result.value = date.today() + timedelta(date_value)
        else:
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
                result.value = today + timedelta(days_ahead)
            elif match_date:
                date_value = int(match_date.group('d'))
                today = date.today()
                days_ahead = date_value - today.day
                if days_ahead < 0:
                    # set the desired day is that day in the next month as default
                    result.value = today.replace(month=today.month + 1, day=date_value)
                else:
                    result.value = date(today.year, today.month, date_value)

    return result

