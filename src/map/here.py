import requests
import logging
from requests.exceptions import HTTPError
from typing import Tuple, List

from ..common.config_manager import ConfigManager
from .entities import SearchResult


logger = logging.getLogger(__name__)


class HereSDK:
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = ConfigManager().get('HERE_API_KEY')
        self.api_key = api_key

    def search(self, at: Tuple[float, float], q: str) -> List[SearchResult]:
        """Get suggestions by query string

        Args:
            at: nearby geo location
            q: query string

        Returns:
            list of SearchResults
        """
        try:
            response = requests.get('https://discover.search.hereapi.com/v1/discover', params={
                'apiKey': self.api_key,
                'at': ','.join(map(str, at)),
                'limit': 10,
                'q': q,
            })
            response.raise_for_status()
            results = []
            for item in response.json()['items']:
                results.append(SearchResult(
                    title=item['title'],
                    address=item['address']['label'],
                    houseNumber=item['address'].get('houseNumber'),
                    street=item['address'].get('street'),
                    district=item['address'].get('district'),
                    city=item['address'].get('city'),
                    latitude=item['position']['lat'],
                    longitude=item['position']['lng'],
                    distance=item['distance']
                ))
            return results
        except HTTPError as e:
            logger.exception(str(e))
            return []

    def geocode(self, housenumber: str, street: str, district: str = None,
                city: str = 'Hồ Chí Minh', country: str = 'VNM'):
        try:
            response = requests.get('https://geocoder.ls.hereapi.com/6.2/geocode.json', params={
                'apiKey': self.api_key,
                'housenumber': housenumber,
                'street': street,
                'district': district,
                'city': city,
                'country': country,
            })
            response.raise_for_status()
            view = response.json()['Response']['View']
            if len(view) > 0:
                results = []
                for res in view[0]['Result']:
                    results.append(SearchResult(
                        title=res['Location']['Address']['Label'],
                        address=res['Location']['Address']['Label'],
                        latitude=res['Location']['DisplayPosition']['Latitude'],
                        longitude=res['Location']['DisplayPosition']['Longitude']))
                return results
            else:
                return []
        except HTTPError as e:
            logger.exception(str(e))
            return []
    
    def reverse_geocode(self, latitude: float, longitude: float) -> SearchResult:
        try:
            response = requests.get('https://revgeocode.search.hereapi.com/v1/revgeocode', params={
                'apiKey': self.api_key,
                'at': '{},{}'.format(latitude, longitude),
                'limit': 1,
            })
            response.raise_for_status()
            results = []
            for item in response.json()['items']:
                results.append(SearchResult(
                    title=item['title'],
                    address=item['address']['label'],
                    houseNumber=item['address'].get('houseNumber'),
                    street=item['address'].get('street'),
                    district=item['address'].get('district'),
                    city=item['address'].get('city'),
                    latitude=item['position']['lat'],
                    longitude=item['position']['lng'],
                    distance=item['distance']
                ))
            return results
        except HTTPError as e:
            logger.exception(str(e))
            return []

    def call_route(self, waypoint0: Tuple[float, float], waypoint1: Tuple[float, float]):
        try:
            response = requests.get('https://route.ls.hereapi.com/routing/7.2/calculateroute.json', params={
                'apiKey': self.api_key,
                'waypoint0': 'geo!{},{}'.format(*waypoint0),
                'waypoint1': 'geo!{},{}'.format(*waypoint1),
            })
            response.raise_for_status()
            return response.json()['Response']['View']
        except HTTPError as e:
            logger.exception(str(e))
            return []
