import datetime
import unittest
from unittest.mock import patch
from datetime import date

from .normalization import normalize, normalize_date, NormalizationError
from src.proto.rest_api_pb2 import Entity


class TestNormalizeDate(unittest.TestCase):
    def setUp(self):
        self.mock_date_patcher = patch('src.dialog_manager.normalization.date')
        self.mock_date = self.mock_date_patcher.start()
        self.mock_date.today.return_value = date(2020, 1, 1)
        self.mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

    def test_date(self):
        entity = 'thứ 5'
        self.assertEqual(normalize_date(entity), date(2020, 1, 2))

    def test_date_2(self):
        entity = 'chủ nhật'
        self.assertEqual(normalize_date(entity), date(2020, 1, 5))

    def test_date_3(self):
        entity = 'thứ 2'
        self.assertEqual(normalize_date(entity), date(2020, 1, 6))

    def test_date_4(self):
        entity = 'hôm nay'
        self.assertEqual(normalize_date(entity), date(2020, 1, 1))

    def test_date_5(self):
        entity = 'mai'
        self.assertEqual(normalize_date(entity), date(2020, 1, 2))

    def test_date_6(self):
        entity = 'mốt'
        self.assertEqual(normalize_date(entity), date(2020, 1, 3))

    def test_date_7(self):
        entity = 'ngày 10'
        self.assertEqual(normalize_date(entity), date(2020, 1, 10))

    def test_date_error(self):
        entity = 'thứ 9'
        with self.assertRaises(NormalizationError):
            normalize_date(entity)

    def test_date_error_2(self):
        entity = 'thứ 1'
        with self.assertRaises(NormalizationError):
            normalize_date(entity)

    def test_date_error_3(self):
        entity = 'thứ một'
        with self.assertRaises(NormalizationError):
            normalize_date(entity)

    def tearDown(self):
        self.mock_date_patcher.stop()


class TestNormalizeNumber(unittest.TestCase):
    def test_result(self):
        entity = Entity()
        entity.name = 'number'
        entity.value = 'đầu tiên'

        self.assertEqual(normalize(None, entity).value, 0)

    def test_result_2(self):
        entity = Entity()
        entity.name = 'number'
        entity.value = '2'

        self.assertEqual(normalize(None, entity).value, 1)
