import logging

from src.dialog_manager.dialog_manager import DialogManager
from src.dialog_manager.response_selector import FirstItemSelector
from src.nlg import NLG
from .call_api import call_nlu, NluException


fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
fh.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(fh)


class CVA:
    def __init__(self):
        self.manager = DialogManager(FirstItemSelector())
        self.nlg = NLG()

    def __call__(self, utterance):
        try:
            intent, entities = call_nlu(utterance)
        except NluException:
            return self.nlg(None, None), None

        response = None
        while response is None:
            response = self.manager.handle(intent, entities,
                                           latitude=10.7720642,
                                           longitude=106.6586572)

        act, data = response
        return self.nlg(act, data), data


if __name__ == '__main__':
    cva = CVA()
    while True:
        utter = input('User: ')
        print('CVA:', cva(utter)[0])
