import numpy as np
import logging
import requests
from datetime import datetime
from fuzzywuzzy import fuzz

from ..common.config_manager import ConfigManager
from ..nlu.intents.constants import Intent
from src.proto.rest_api_pb2 import Entity


logger = logging.getLogger(__name__)


def call_nlu(text: str):
    """Call NLU from remote URL"""
    nlu_url = ConfigManager().get('NLU_URL')

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
    distance = fuzz.partial_ratio(target, value)
    if distance >= 90:
        return True
    return False


def datetime_range_to_string(d1: datetime, d2: datetime) -> str:
    if d1.time() == datetime.min.time() and d2.time() == datetime.min.time():
        return d1.strftime('ngày %d tháng %m')
    return 'Thời gian đó'