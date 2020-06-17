import numpy as np
from typing import List, Dict, Union, Tuple, Any, Iterator


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

    def get_state(self, slot_name: str = None, default_value: any = None):
        lasts = {}
        for slot, value in self.history:
            lasts[slot] = value
        if slot_name is not None:
            return lasts.get(slot_name, default_value)
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
