from src.dialog_manager.dialog_manager import DialogManager
from src.dialog_manager.response_selector import FirstItemSelector
from src.nlg import NLG
from .call_api import call_nlu


class CVA:
    def __init__(self):
        self.manager = DialogManager(FirstItemSelector())
        self.nlg = NLG()

    def __call__(self, utterance):
        intent, entities = call_nlu(utterance)

        act, data = self.manager.handle(intent, entities,
                                        latitude=10.7720642,
                                        longitude=106.6586572)

        return self.nlg(act, data), data


if __name__ == '__main__':
    cva = CVA()
    utter = input('User: ')
    print('CVA:', cva(utter)[0])
