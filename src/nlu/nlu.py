import re
from typing import List

from .intents.constants import Intent
from .bert.predict import BertPredictor
from src.proto.rest_api_pb2 import Entity
from .common import MODEL_DIR, PHONE_CALL_REGEX, PHONE_TEXT_REGEX, SELECT_ITEM_REGEX, YES_REGEX, NO_REGEX


class NLU:
    def __init__(self):
        self.nlu_model = BertPredictor()

    def predict(self, text: str) -> List[Entity]:
        """Predict intent of a string & extract entities"""
        # Use regex matching first
        intent_result = None
        regex_list = [
            (PHONE_CALL_REGEX, Intent.phone_call),
            (PHONE_TEXT_REGEX, Intent.phone_text),
            (SELECT_ITEM_REGEX, Intent.select_item),
            (YES_REGEX, Intent.yes),
            (NO_REGEX, Intent.no),
        ]
        for patterns, intent in regex_list:
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    intent_result = intent
            if intent_result is not None:
                break

        ner_results = []
        for pattern in PHONE_CALL_REGEX + PHONE_TEXT_REGEX + SELECT_ITEM_REGEX:
            search_res = re.search(pattern, text, re.IGNORECASE)
            if search_res:
                for name, value in search_res.groupdict().items():
                    entity = Entity()
                    entity.name = name
                    entity.value = value
                    ner_results.append(entity)
                break

        if intent_result is not None:
            return intent_result, ner_results

        # If not match, use model
        intent_result, ner_results = self.nlu_model.predict(text)
        return Intent(intent_result), self._convert_bert_predictions_to_entities_list(ner_results)

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
