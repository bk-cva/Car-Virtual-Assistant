import re
import spacy
import pickle
import os.path
from typing import List

from .intents.regexer import classify_by_regex
from .intents.constants import Intent
from .entities.constants import PHONE_CALL_REGEX, PHONE_TEXT_REGEX
from .entities.bert_ner import BertNER
from src.proto.rest_api_pb2 import Entity
from .common import MODEL_DIR


class NLU:
    def __init__(self):
        self.ner_model = BertNER()
        self.nlp = spacy.load('vi_spacy_model')
        self.intent_model = pickle.load(open(os.path.join(MODEL_DIR, 'clf.sav'), mode='rb'))

    def predict_intent(self, text: str) -> Intent:
        """Predict intent of a string"""
        regex_intent = classify_by_regex(text)
        if regex_intent:
            return Intent(regex_intent)
        x = self.nlp(text).vector
        return Intent(self.intent_model.predict([x])[0])

    def predict_entity(self, text: str) -> List[Entity]:
        results = []
        for pattern in PHONE_CALL_REGEX:
            search_res = re.search(pattern, text, re.IGNORECASE)
            if search_res:
                entity = Entity()
                entity.name = 'person_name'
                entity.value = search_res.group(1)

                results.append(entity)
                break

        for pattern in PHONE_TEXT_REGEX:
            search_res = re.search(pattern, text, re.IGNORECASE)
            if search_res:
                entity = Entity()
                entity.name = 'person_name'
                entity.value = search_res.group(1)

                entity2 = Entity()
                entity2.name = 'message'
                entity2.value = search_res.group(2)

                results.append(entity)
                results.append(entity2)
                break

        bert_predictions = self.ner_model.predict(text)
        bert_results = []
        for i, bert_predict in enumerate(bert_predictions):
            if bert_predict[1] != 'O':
                if bert_predict[1].startswith('B-'):
                    entity = Entity()
                    entity.name = bert_predict[1][2:]
                    entity.value = bert_predict[0]
                    bert_results.append(entity)
                elif bert_predict[1].startswith('I-') and i > 0 and re.match(r'^[BI]-', bert_predictions[i - 1][1]):
                    bert_results[-1].value += ' ' + bert_predict[0]

        return results + bert_results
