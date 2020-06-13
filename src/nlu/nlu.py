import re
import spacy
import pickle
import os.path
from typing import List

from .intents.constants import Intent
from .entities.bert_ner import BertNER
from src.proto.rest_api_pb2 import Entity
from .common import MODEL_DIR, PHONE_CALL_REGEX, PHONE_TEXT_REGEX, SELECT_ITEM_REGEX


class NLU:
    def __init__(self):
        self.ner_model = BertNER()
        self.nlp = spacy.load('vi_spacy_model')
        self.intent_model = pickle.load(open(os.path.join(MODEL_DIR, 'clf.sav'), mode='rb'))

    def predict_intent(self, text: str) -> Intent:
        """Predict intent of a string"""
        for pattern in PHONE_CALL_REGEX:
            if re.search(pattern, text, re.IGNORECASE):
                return Intent.phone_call
        for pattern in PHONE_TEXT_REGEX:
            if re.search(pattern, text, re.IGNORECASE):
                return Intent.phone_text
        for pattern in SELECT_ITEM_REGEX:
            if re.search(pattern, text, re.IGNORECASE):
                return Intent.select_item

        x = self.nlp(text).vector
        return Intent(self.intent_model.predict([x])[0])

    def predict_entities(self, text: str) -> List[Entity]:
        """Extract entities"""
        results = []
        for pattern in PHONE_CALL_REGEX + PHONE_TEXT_REGEX + SELECT_ITEM_REGEX:
            search_res = re.search(pattern, text, re.IGNORECASE)
            if search_res:
                for name, value in search_res.groupdict().items():
                    entity = Entity()
                    entity.name = name
                    entity.value = value
                    results.append(entity)
                break
        if len(results) > 0:
            return results

        bert_predictions = self.ner_model.predict(text)
        return self._convert_bert_predictions_to_entities_list(bert_predictions)

    @staticmethod
    def _convert_bert_predictions_to_entities_list(bert_predictions) -> List[Entity]:
        entities_list = []
        for i, bert_predict in enumerate(bert_predictions):
            entity_name, entity_value = bert_predict
            previous_entity_name = bert_predictions[i - 1][0]
            if entity_name.startswith('B-') or \
                (
                    # In case of wrong predictions
                    # For example: I-a I-a, O I-a, I-a I-b
                    entity_name.startswith('I-') and \
                    (
                        i == 0 or \
                        not re.match(r'^[BI]-', previous_entity_name) or
                        (
                            re.match(r'^[BI]-', previous_entity_name) and
                            entity_name[2:] != previous_entity_name[2:]
                        )
                    )
            ):
                entity = Entity()
                entity.name = entity_name[2:]
                entity.value = entity_value
                entities_list.append(entity)
            elif entity_name.startswith('I-'):
                entities_list[-1].value += ' ' + entity_value
        return entities_list
