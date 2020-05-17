from typing import Tuple


class SearchResult:
    def __init__(self,
                 title: str,
                 address: str = None,
                 houseNumber: str = None,
                 street: str = None,
                 district: str = None,
                 city: str = None,
                 latitude: float = None,
                 longitude: float = None,
                 distance: float = None,
                 **kwargs):
        self.title = title
        self.address = address
        self.houseNumber = houseNumber
        self.street = street
        self.district = district
        self.city = city
        self.latitude = latitude
        self.longitude = longitude
        self.distance = distance
