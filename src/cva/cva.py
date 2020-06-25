import logging
from datetime import date
from unittest.mock import patch

from src.config_manager import ConfigManager
from src.nlu import NLU
from src.utils import call_external_nlu, NluException
from src.dialog_manager.normalization import normalize
from src.dialog_manager.dialog_manager import DialogManager
from src.nlg import NLG


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class CVA:
    def __init__(self, do_call_external_nlu: bool = True):
        self.manager = DialogManager()
        self.nlg = NLG()
        self.do_call_external_nlu = do_call_external_nlu
        if self.do_call_external_nlu:
            self.nlu_url = ConfigManager().get('NLU_URL')
        else:
            self.nlu = NLU()

    def reset(self):
        logger.debug('Reset state.')
        self.manager.reset_state()

    def __call__(self, utterance: str, latitude: float = 10.7720642, longitude: float = 106.6586572):
        try:
            if self.do_call_external_nlu:
                intent, entities = call_external_nlu(self.nlu_url, utterance)
            else:
                intent, entities = self.nlu.predict(utterance)
        except NluException:
            return self.nlg(None, {}), {}, None

        entities = list(map(lambda e: normalize(intent, e), entities))

        response = None
        while response is None:
            response = self.manager.handle(intent, entities,
                                           latitude=latitude,
                                           longitude=longitude)

        act, data = response
        return self.nlg(act, data), data, intent, act
