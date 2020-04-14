import os
import requests
from dotenv import load_dotenv

from ..nlu.intents.constants import Intent
from src.proto.rest_api_pb2 import Entity


load_dotenv()


def call_nlu(text: str):
    nlu_url = os.getenv('NLU_URL')
    res = requests.post(nlu_url, json={
        'texts': [text]
    }).json()['results'][0]

    entities = []
    for entity in res['entity']:
        entities.append(Entity())
        entities[-1].name = entity['name']
        entities[-1].value = entity['value']
    return Intent(res['intentId']), entities
