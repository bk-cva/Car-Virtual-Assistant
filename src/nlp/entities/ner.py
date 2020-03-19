import re
from typing import List

from .constants import PHONE_CALL_REGEX, PHONE_TEXT_REGEX
from src.proto.rest_api_pb2 import Entity


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

    return results
