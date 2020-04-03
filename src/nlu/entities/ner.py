import re
from typing import List

from .constants import PHONE_CALL_REGEX, PHONE_TEXT_REGEX
from src.proto.rest_api_pb2 import Entity
from .bert_ner import predict


def predict_entity(text: str) -> List[Entity]:
    results = []
    for pattern in PHONE_CALL_REGEX:
        search_res = re.search(pattern, text, re.IGNORECASE)
        if search_res:
            entity = Entity()
            entity.name = 'person_name'
            entity.value = search_res.group(1)

            results.append(entity)
            break

    for pattern in PHONE_TEXT_REGEX:
        search_res = re.search(pattern, text, re.IGNORECASE)
        if search_res:
            entity = Entity()
            entity.name = 'person_name'
            entity.value = search_res.group(1)

            entity2 = Entity()
            entity2.name = 'message'
            entity2.value = search_res.group(2)

            results.append(entity)
            results.append(entity2)
            break

    bert_predictions = predict(text)
    bert_results = []
    for i, bert_predict in enumerate(bert_predictions):
        if bert_predict[1] != 'O':
            if bert_predict[1].startswith('B-'):
                entity = Entity()
                entity.name = bert_predict[1][2:]
                entity.value = bert_predict[0]
                bert_results.append(entity)
            elif bert_predict[1].startswith('I-') and i > 0 and re.match(r'^[BI]-', bert_predictions[i - 1][1]):
                bert_results[-1].value += ' ' + bert_predict[0]

    return results + bert_results
