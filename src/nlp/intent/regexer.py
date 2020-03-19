import re
from typing import Optional

from .constants import Intent, LOCATION_REGEX, ACTION_REGEX


def classify_by_regex(text: str) -> Optional[Intent]:
    # for pattern in LOCATION_REGEX:
    #     if re.search(pattern, text, re.IGNORECASE):
    #         return Intent.location
    # for pattern in ACTION_REGEX:
    #     if re.search(pattern, text, re.IGNORECASE):
    #         return Intent.action
    return None
