import re
from typing import List, Tuple

from .intent import Intent
from .entity import entity_factory
from src.proto.rest_api_pb2 import Entity
from .bert.predict import BertPredictor
from .regexes import regex_list


class NLU:
    def __init__(self):
        self.nlu_model = BertPredictor('/models')

    def predict(self, text: str) -> Tuple[Intent, List[Entity]]:
        """Predict intent & extract entities of a string"""
        # Use regex matching first
        intent_result = self.predict_intent_by_regex(text)
        ner_results = self.predict_ner_by_regex(text)
        if intent_result is not None:
            return intent_result, ner_results

        # If not match, use model
        intent_result, ner_results = self.nlu_model.predict(text)
        return Intent(intent_result), self._convert_bert_predictions_to_entities_list(ner_results)

    @classmethod
    def predict_intent_by_regex(cls, text: str):
        for patterns, intent in regex_list:
            for pattern in patterns:
                if cls.search_ignore_case(text, pattern):
                    return intent
        return None

    @classmethod
    def predict_ner_by_regex(cls, text: str):
        ner_results = []
        for pattern in [pattern for patterns, intent in regex_list for pattern in patterns]:
            search_res = cls.search_ignore_case(text, pattern)
            if search_res:
                for name, value in search_res.groupdict().items():
                    entity = entity_factory(name, value)
                    ner_results.append(entity)
                break
        return ner_results

    @staticmethod
    def search_ignore_case(text, pattern):
        return re.search(pattern, text, re.IGNORECASE)

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
                entity = entity_factory(entity_name[2:], entity_value)
                entities_list.append(entity)
            elif entity_name.startswith('I-'):
                entities_list[-1].value += ' ' + entity_value
        return entities_list
