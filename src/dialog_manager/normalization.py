import re
from datetime import date, timedelta

from src.proto.rest_api_pb2 import Entity


NORMALIZE_ENTITY_DICT = {
    'number': {
        1: ['1', 'nhất', 'đầu tiên', 'một'],
        2: ['2', 'hai', 'nhì'],
        3: ['3', 'ba'],
        4: ['4', 'bốn', 'tư'],
        5: ['5', 'năm'],
        6: ['6', 'sáu'],
        7: ['7', 'bảy'],
        8: ['8', 'tám'],
        9: ['9', 'chín'],
        10: ['10', 'mười'],
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


def normalize(entity: Entity):
    if entity.name in NORMALIZE_ENTITY_DICT:
        for normalized_value, possible_values in NORMALIZE_ENTITY_DICT[entity.name].items():
            if entity.value in possible_values:
                entity.value = normalized_value

    if entity.name == 'date':
        date_value = entity.value
        if isinstance(date_value, int):
            entity.value = date.today() + timedelta(date_value)
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
                entity.value = today + timedelta(days_ahead)
            elif match_date:
                date_value = int(match_date.group('d'))
                today = date.today()
                days_ahead = date_value - today.day
                if days_ahead < 0:
                    # TODO: handle next month
                    raise NormalizationError()
                entity.value = date(today.year, today.month, date_value)

    return entity

