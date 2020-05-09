import logging

from src.dialog_manager.dialog_manager import DialogManager
from src.dialog_manager.normalization import normalize
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

        entities = list(map(normalize, entities))

        response = None
        while response is None:
            response = self.manager.handle(intent, entities,
                                           latitude=10.7720642,
                                           longitude=106.6586572)

        act, data = response
        return self.nlg(act, data), data


if __name__ == '__main__':
    cva = CVA()
    user_snapshot = []
    with open('snapshots/user_snapshot.txt', mode='r', encoding='utf-8') as file:
        user_conversation = []
        while True:
            line = file.readline()
            if not line:
                if len(user_conversation) > 0:
                    user_snapshot.append(user_conversation)
                break
            if len(line.strip()) > 0:
                user_conversation.append(line)
            else:
                user_snapshot.append(user_conversation)
                user_conversation = []

    with open('snapshots/cva_snapshot.txt', mode='w', encoding='utf-8') as file:
        while True:
            if len(user_snapshot) == 0:
                break
            user_conversation = user_snapshot.pop(0)
            for utter in user_conversation:
                cva_response = cva(utter)[0]
                file.write(cva_response + '\n')
            file.write('\n')
            cva.manager.reset_state()

