import datetime
import unittest
from unittest.mock import patch
from datetime import date

from.normalization import normalize, NormalizationError
from src.proto.rest_api_pb2 import Entity


class TestNormalizeDate(unittest.TestCase):
    def setUp(self):
        self.mock_date_patcher = patch('src.dialog_manager.normalization.date')
        self.mock_date = self.mock_date_patcher.start()
        self.mock_date.today.return_value = date(2020, 1, 1)
        self.mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    def test_date(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'thứ 5'

        result = normalize(entity)
        self.assertEqual(result, date(2020, 1, 2))

    def test_date_2(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'chủ nhật'

        result = normalize(entity)
        self.assertEqual(result, date(2020, 1, 5))

    def test_date_3(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'thứ 2'

        result = normalize(entity)
        self.assertEqual(result, date(2020, 1, 6))

    def test_date_4(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'hôm nay'

        result = normalize(entity)
        self.assertEqual(result, date(2020, 1, 1))

    def test_date_5(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'mai'

        result = normalize(entity)
        self.assertEqual(result, date(2020, 1, 2))

    def test_date_6(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'mốt'

        result = normalize(entity)
        self.assertEqual(result, date(2020, 1, 3))

    def test_date_7(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'ngày 10'

        result = normalize(entity)
        self.assertEqual(result, date(2020, 1, 10))
    
    def test_date_error(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'thứ 9'

        with self.assertRaises(NormalizationError):
            normalize(entity)
    
    def test_date_error_2(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'thứ 1'

        with self.assertRaises(NormalizationError):
            normalize(entity)
    
    def test_date_error_3(self):
        entity = Entity
        entity.name = 'date'
        entity.value = 'thứ một'

        with self.assertRaises(NormalizationError):
            normalize(entity)


    def tearDown(self):
        self.mock_date_patcher.stop()
