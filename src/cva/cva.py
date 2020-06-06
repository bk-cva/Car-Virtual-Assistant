import logging
from datetime import date
from unittest.mock import patch

from src.dialog_manager.dialog_manager import DialogManager
from src.dialog_manager.normalization import normalize
from src.dialog_manager.response_selector import FirstItemSelector
from src.nlg import NLG
from src.utils import call_nlu, NluException


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CVA:
    def __init__(self):
        self.manager = DialogManager(FirstItemSelector())
        self.nlg = NLG()

    def reset(self):
        logger.debug('Reset state.')
        self.manager.reset_state()

    def __call__(self, utterance: str, latitude: float = 10.7720642, longitude: float = 106.6586572):
        try:
            intent, entities = call_nlu(utterance)
        except NluException:
            return self.nlg(None, None), None

        entities = list(map(lambda e: normalize(intent, e), entities))

        response = None
        while response is None:
            response = self.manager.handle(intent, entities,
                                           latitude=latitude,
                                           longitude=longitude)

        act, data = response
        return self.nlg(act, data), data, intent
