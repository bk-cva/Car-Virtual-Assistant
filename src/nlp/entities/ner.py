import re
from typing import List

from .constants import PLACE_REGEX, STREET_REGEX, WARD_REGEX, DISTRICT_REGEX
from src.proto.rest_api_pb2 import Entity


def predict_entity(text: str) -> List[Entity]:
    results = []
    for place in PLACE_REGEX:
        pattern = '%s (.+)' % place
        if re.search(pattern, text, re.IGNORECASE):
            entity = Entity()
            entity.name = 'place'
            entity.value = place
            entity2 = Entity()
            entity2.name = 'place_name'
            entity2.value = re.search(pattern, text, re.IGNORECASE).group(1)
            results.append(entity)
            results.append(entity2)
            break

    for street in STREET_REGEX:
        pattern = '%s (.+)' % street
        if re.search(pattern, text, re.IGNORECASE):
            entity = Entity()
            entity.name = 'street'
            entity.value = re.search(pattern, text, re.IGNORECASE).group(1)
            results.append(entity)
            break

    for ward in WARD_REGEX:
        pattern = '%s (.+)' % ward
        if re.search(pattern, text, re.IGNORECASE):
            entity = Entity()
            entity.name = 'ward'
            entity.value = re.search(pattern, text, re.IGNORECASE).group(1)
            results.append(entity)
            break

    for district in DISTRICT_REGEX:
        pattern = '%s (.+)' % district
        if re.search(pattern, text, re.IGNORECASE):
            entity = Entity()
            entity.name = 'district'
            entity.value = re.search(pattern, text, re.IGNORECASE).group(1)
            results.append(entity)
            break

    return results
