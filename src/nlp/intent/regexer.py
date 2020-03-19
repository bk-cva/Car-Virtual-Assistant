import re
from typing import Optional

from .constants import Intent, PHONE_CALL_REGEX, PHONE_TEXT_REGEX


def classify_by_regex(text: str) -> Optional[Intent]:
    for pattern in PHONE_CALL_REGEX:
        if re.search(pattern, text, re.IGNORECASE):
            return Intent.phone_call
    for pattern in PHONE_TEXT_REGEX:
        if re.search(pattern, text, re.IGNORECASE):
            return Intent.phone_text
    return None
