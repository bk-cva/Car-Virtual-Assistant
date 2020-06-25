import numpy as np
import logging
import requests
from datetime import datetime, date
from fuzzywuzzy import fuzz

from ..nlu.intent import Intent
from src.proto.rest_api_pb2 import Entity


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def call_external_nlu(nlu_url: str, text: str):
    """Call NLU from remote URL"""
    try:
        payload = {'texts': [text]}
        res = requests.post(nlu_url, json=payload)
        res.raise_for_status()
        res = res.json()['results'][0]
    except Exception as e:
        logger.exception(
            'Exception occured when sending message: "{}"'.format(text))
        logger.exception(str(e))
        raise NluException()

    entities = []
    if 'entity' in res:
        for entity in res['entity']:
            entities.append(Entity())
            entities[-1].name = entity['name']
            entities[-1].value = entity['value']
    return Intent(res['intent']), entities


class NluException(Exception):
    pass


def match_string(target: str, value: str) -> bool:
    distance = fuzz.ratio(target.lower(), value.lower())
    logger.debug('Search term: {}. Result: {}. Distance: {}'.format(target, value, distance))
    if distance >= 90:
        return True
    return False


def datetime_to_time_string(d: datetime) -> str:
    result = ''
    if d.minute == 0:
        result += d.strftime('%H giờ')
    else:
        if d.minute == 30:
            result += d.strftime('%H giờ rưỡi')
        else:
            result += d.strftime('%H giờ %M phút')
    
    if d.date() == date.today():
        result += ' hôm nay'
    else:
        result += ' ngày {}'.format(d.date().day)

    if d.date().month != date.today().month:
        result += ' tháng {}'.format(d.date().month)

    return result
