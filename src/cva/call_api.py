import requests

from ..common.config_manager import ConfigManager
from ..nlu.intents.constants import Intent
from src.proto.rest_api_pb2 import Entity


def call_nlu(text: str):
    nlu_url = ConfigManager().get('NLU_URL')
    res = requests.post(nlu_url, json={
        'texts': [text]
    }).json()['results'][0]

    entities = []
    for entity in res['entity']:
        entities.append(Entity())
        entities[-1].name = entity['name']
        entities[-1].value = entity['value']
    return Intent(res['intentId']), entities
