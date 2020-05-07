from typing import Tuple


class SuggestionResult:
    def __init__(self,
                 title: str,
                 vicinity: str = None,
                 position: Tuple[float, float] = None,
                 distance: float = None,
                 **kwargs):
        self.title = title
        self.vicinity = vicinity
        self.position = position
        self.distance = distance
