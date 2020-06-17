import re
from enum import Enum
from typing import Tuple


class Place:
    def __init__(self,
                 title: str,
                 address: str,
                 latitude: float,
                 longitude: float):
        self.title = title
        self.address = address
        self.latitude = latitude
        self.longitude = longitude

class HerePlace(Place):
    def __init__(self, item: dict):
        address = item.get('address', {})
        super().__init__(
            title=item.get('title'),
            address=address.get('label'),
            latitude=item['position']['lat'],
            longitude=item['position']['lng'])
        self.id = item.get('id')
        self.access = item.get('access', [])
        self.distance = item.get('distance')
        self.houseNumber = address.get('houseNumber', '')
        self.street = re.sub(r'^đường', '', address.get('street', ''), flags=re.IGNORECASE).strip()
        self.district = address.get('district')
        self.city = address.get('city')
        self.categories = []
        for cat in item.get('categories', []):
            try:
                place_cat = PlaceCategory(cat['id'][:8])
            except ValueError:
                place_cat = PlaceCategory.Others
            self.categories.append(place_cat)


class PlaceCategory(str, Enum):
    """Map an id to the specific place category based on HERE Documentation
    https://developer.here.com/documentation/places/dev_guide/topics/place_categories/places-category-system.html
    """
    Restaurant = '100-1000'
    CoffeeTea = '100-1100'
    NightlifeEntertainment = '200-2000'
    Cinema = '200-2100'
    ConvenienceStore = '600-6000'
    ShoppingMall = '600-6100'
    DepartmentStore = '600-6200'
    DrugstorePharmacy = '600-6400'
    Hospital = '800-8000'
    Others = 'Others'

