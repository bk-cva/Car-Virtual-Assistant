from typing import Tuple


class SearchResult:
    def __init__(self,
                 title: str,
                 address: str = None,
                 latitude: float = None,
                 longitude: float = None,
                 distance: float = None,
                 **kwargs):
        self.title = title
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.distance = distance
