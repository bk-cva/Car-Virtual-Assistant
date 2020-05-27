import requests
import logging
from requests.exceptions import HTTPError
from typing import Tuple, List

from ..common.config_manager import ConfigManager
from .entities import HerePlace, Place


logger = logging.getLogger(__name__)


class HereSDK:
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = ConfigManager().get('HERE_API_KEY')
        self.api_key = api_key

    def search(self, at: Tuple[float, float], q: str, limit: int = 3) -> List[HerePlace]:
        """Search places by query

        Args:
            at: nearby geo location
            q: query string
            limit: maximum number of results

        Returns:
            list of HerePlace
        """
        try:
            response = requests.get('https://discover.search.hereapi.com/v1/discover', params={
                'apiKey': self.api_key,
                'at': ','.join(map(str, at)),
                'limit': limit,
                'q': q,
            })
            response.raise_for_status()
            results = []
            for item in response.json()['items']:
                results.append(HerePlace(item))
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
                    results.append(Place(
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
    
    def reverse_geocode(self, latitude: float, longitude: float) -> List[HerePlace]:
        try:
            response = requests.get('https://revgeocode.search.hereapi.com/v1/revgeocode', params={
                'apiKey': self.api_key,
                'at': '{},{}'.format(latitude, longitude),
                'limit': 1,
            })
            response.raise_for_status()
            results = []
            for item in response.json()['items']:
                results.append(HerePlace(item))
            return results
        except HTTPError as e:
            logger.exception(str(e))
            return []

    def calculate_route(self, origin: Tuple[float, float], destination: Tuple[float, float]):
        try:
            response = requests.get('https://router.hereapi.com/v8/routes', params={
                'apiKey': self.api_key,
                'origin': '{},{}'.format(*origin),
                'destination': '{},{}'.format(*destination),
                'transportMode': 'car',
                'lang': 'vi',
                'return': 'polyline,actions,instructions'
            })
            response.raise_for_status()
            return response.json()['routes'][0]['sections']
        except HTTPError as e:
            logger.exception(str(e))
            return []
