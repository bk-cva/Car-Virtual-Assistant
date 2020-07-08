import datetime
import unittest
from unittest.mock import patch
from datetime import date

from .nlu import NLU
from .intent import Intent
from src.proto.rest_api_pb2 import Entity


def new_entity(name, value):
    entity = Entity()
    entity.name = name
    entity.value = value
    return entity


class TestPredictIntentByRegex(unittest.TestCase):
    def test_intent_select_item(self):
        intent = NLU.predict_intent_by_regex('cái thứ nhất')
        self.assertEqual(intent, Intent.select_item)

    def test_intent_yes(self):
        intent = NLU.predict_intent_by_regex('có')
        self.assertEqual(intent, Intent.yes)

    def test_intent_unknown(self):
        intent = NLU.predict_intent_by_regex('hihihi')
        self.assertEqual(intent, None)


class TestPredictNerByRegex(unittest.TestCase):
    def test_ner_select_item(self):
        entities = NLU.predict_ner_by_regex('cái thứ nhất')
        self.assertListEqual(entities, [new_entity('number', 'nhất')])

    def test_ner_yes(self):
        entities = NLU.predict_ner_by_regex('có')
        self.assertListEqual(entities, [])

    def test_ner_unknown(self):
        entities = NLU.predict_ner_by_regex('hihihi')
        self.assertEqual(entities, [])


class TestConvertBertPredictionsToEntitiesList(unittest.TestCase):
    def test_empty(self):
        predictions = []
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [])

    def test_B(self):
        predictions = [('B-x', 'a')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a')])

    def test_B_B(self):
        predictions = [('B-x', 'a'), ('B-x', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a'), new_entity('x', 'b')])

    def test_B_B_2(self):
        predictions = [('B-x', 'a'), ('B-y', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a'), new_entity('y', 'b')])

    def test_B_I(self):
        predictions = [('B-x', 'a'), ('I-x', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a b')])

    def test_B_I_2(self):
        predictions = [('B-x', 'a'), ('I-y', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a'), new_entity('y', 'b')])

    def test_B_O(self):
        predictions = [('B-x', 'a'), ('O', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a')])

    def test_B_I_I(self):
        predictions = [('B-x', 'a'), ('I-x', 'b'), ('I-x', 'c')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a b c')])

    def test_B_I_I_2(self):
        predictions = [('B-x', 'a'), ('I-x', 'b'), ('I-y', 'c')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a b'), new_entity('y', 'c')])

    def test_B_O_B(self):
        predictions = [('B-x', 'a'), ('O', 'o'), ('B-x', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a'), new_entity('x', 'b')])

    def test_B_O_I(self):
        predictions = [('B-x', 'a'), ('O', 'o'), ('I-x', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a'), new_entity('x', 'b')])

    def test_O(self):
        predictions = [('O', 'o')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [])

    def test_O_B(self):
        predictions = [('O', 'o'), ('B-x', 'a')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a')])

    def test_O_I(self):
        predictions = [('O', 'o'), ('I-x', 'a')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a')])

    def test_O_O(self):
        predictions = [('O', 'o'), ('O', 'o')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [])

    def test_O_B_I(self):
        predictions = [('O', 'o'), ('B-x', 'a'), ('I-x', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a b')])

    def test_O_I_I(self):
        predictions = [('O', 'o'), ('I-x', 'a'), ('I-x', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a b')])

    def test_O_I_I_2(self):
        predictions = [('O', 'o'), ('I-x', 'a'), ('I-y', 'b')]
        entities = NLU._convert_bert_predictions_to_entities_list(predictions)
        self.assertEqual(entities, [new_entity('x', 'a'), new_entity('y', 'b')])
