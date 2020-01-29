import re

from src.nlp.intent_classification.constants import Intent, LOCATION_REGEX, ACTION_REGEX


def classify_intent(text: str) -> Intent:
    for pattern in LOCATION_REGEX:
        if re.search(pattern, text, re.IGNORECASE):
            return Intent.location
    for pattern in ACTION_REGEX:
        if re.search(pattern, text, re.IGNORECASE):
            return Intent.action
    return Intent.others
