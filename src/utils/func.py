import numpy as np
import logging
import requests

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


def levenshtein(seq1: str, seq2: str):
    """Calculate Levenshtein distance between 2 strings"""
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros((size_x, size_y))
    for x in range(size_x):
        matrix[x, 0] = x
    for y in range(size_y):
        matrix[0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x-1] == seq2[y-1]:
                matrix[x, y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix[x, y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1] + 1,
                    matrix[x, y-1] + 1
                )

    return (matrix[size_x - 1, size_y - 1])
