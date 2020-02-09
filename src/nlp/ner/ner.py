import re
from typing import Dict

from src.nlp.ner.constants import PLACE_REGEX, STREET_REGEX, WARD_REGEX, DISTRICT_REGEX


def ner(text: str) -> Dict:
    results = {}
    for place in PLACE_REGEX:
        pattern = '%s (.+)' % place
        if re.search(pattern, text, re.IGNORECASE):
            results['place'] = place
            results['place_name'] = re.search(pattern, text, re.IGNORECASE).group(1)
            break

    for street in STREET_REGEX:
        pattern = '%s (.+)' % street
        if re.search(pattern, text, re.IGNORECASE):
            results['street'] = re.search(pattern, text, re.IGNORECASE).group(1)
            break

    for ward in WARD_REGEX:
        pattern = '%s (.+)' % ward
        if re.search(pattern, text, re.IGNORECASE):
            results['ward'] = re.search(pattern, text, re.IGNORECASE).group(1)
            break

    for district in DISTRICT_REGEX:
        pattern = '%s (.+)' % district
        if re.search(pattern, text, re.IGNORECASE):
            results['district'] = re.search(pattern, text, re.IGNORECASE).group(1)
            break

    return results
