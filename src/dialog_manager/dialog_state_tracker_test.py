import unittest
from numpy.testing import assert_array_equal

from .dialog_state_tracker import FeaturizedTracker


class TestFeaturizedTracker(unittest.TestCase):
    def test_property(self):
        tracker = FeaturizedTracker(['a', 'b', 'c'])

        self.assertEqual(tracker.state_size, 3)

    def test_update_state_by_list(self):
        tracker = FeaturizedTracker(['a', 'b', 'c'])
        tracker.update_state([('a', 1), ('b', 2), ('d', 4)])

        self.assertListEqual(tracker.history, [('a', 1), ('b', 2)])

    def test_update_state_by_dict(self):
        tracker = FeaturizedTracker(['a', 'b', 'c'])
        tracker.update_state({'a': 1, 'b': 2, 'd': 4})

        self.assertListEqual(tracker.history, [('a', 1), ('b', 2)])

    def test_get_state_and_features(self):
        tracker = FeaturizedTracker(['a', 'b', 'c'])

        self.assertDictEqual(tracker.get_state(), {})
        assert_array_equal(tracker.get_features(), [0, 0, 0])

        tracker.update_state({'a': 1, 'b': 2, 'd': 4})

        self.assertDictEqual(tracker.get_state(), {'a': 1, 'b': 2})
        assert_array_equal(tracker.get_features(), [1, 1, 0])

        tracker.update_state({'a': 3, 'b': 1, 'c': 4})

        self.assertDictEqual(tracker.get_state(), {'a': 3, 'b': 1, 'c': 4})
        assert_array_equal(tracker.get_features(), [1, 1, 1])

    def test_reset_state(self):
        tracker = FeaturizedTracker(['a', 'b', 'c'])
        tracker.update_state({'a': 1, 'b': 2, 'd': 4})

        self.assertDictEqual(tracker.get_state(), {'a': 1, 'b': 2})
        assert_array_equal(tracker.get_features(), [1, 1, 0])

        tracker.reset_state()

        self.assertDictEqual(tracker.get_state(), {})
        assert_array_equal(tracker.get_features(), [0, 0, 0])
