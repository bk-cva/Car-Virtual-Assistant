import unittest
import numpy as np
from numpy.testing import assert_array_equal
from logging import getLogger
from typing import List, Dict, Union, Tuple, Any, Iterator

log = getLogger(__name__)


class FeaturizedTracker:
    """
    Tracker that overwrites slots with new values.
    Features are binary features (slot is present/absent).

    Parameters:
        slot_names: list of slots that should be tracked.
    """

    def __init__(self, slot_names: List[str]) -> None:
        self.slot_names = list(slot_names)
        self.history = []
        self.current_features = np.zeros(self.state_size, dtype=np.float32)

    @property
    def state_size(self) -> int:
        return len(self.slot_names)

    @property
    def is_full(self) -> bool:
        return self.state_size == np.sum(self.current_features)

    def update_state(self, slots: Union[Iterator[Tuple[str, any]], Dict]):
        if isinstance(slots, list):
            self.history.extend(self._filter(slots))

        elif isinstance(slots, dict):
            for slot, value in self._filter(slots.items()):
                self.history.append((slot, value))

        bin_feats = self._binary_features()

        self.current_features = bin_feats

    def get_state(self):
        lasts = {}
        for slot, value in self.history:
            lasts[slot] = value
        return lasts

    def reset_state(self):
        self.history = []
        self.current_features = np.zeros(self.state_size, dtype=np.float32)

    def get_features(self):
        return self.current_features

    def _filter(self, slots) -> Iterator:
        return filter(lambda s: s[0] in self.slot_names, slots)

    def _binary_features(self) -> np.ndarray:
        feats = np.zeros(self.state_size, dtype=np.float32)
        lasts = self.get_state()
        for i, slot in enumerate(self.slot_names):
            if slot in lasts:
                feats[i] = 1.
        return feats


if __name__ == '__main__':
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


    unittest.main()
