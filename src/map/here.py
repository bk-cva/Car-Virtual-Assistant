import requests
import logging
from requests.exceptions import HTTPError
from typing import Tuple, List

from ..common.config_manager import ConfigManager
from .entities import SuggestionResult


logger = logging.getLogger(__name__)


class HereSDK:
    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = ConfigManager().get('HERE_API_KEY')
        self.api_key = api_key

    def call_autosuggest(self, at: Tuple[float, float], q: str) -> List[SuggestionResult]:
        """Get suggestions by query string

        Args:
            at: nearby geo location
            q: query string

        Returns:
            list of SuggestionResults
        """
        try:
            response = requests.get('https://places.sit.ls.hereapi.com/places/v1/discover/search', params={
                'apiKey': self.api_key,
                'tf': 'plain',
                'at': ','.join(map(str, at)),
                'q': q,
            })
            response.raise_for_status()
            results = []
            for res in response.json()['results']['items']:
                results.append(SuggestionResult(**res))
            return results
        except HTTPError as e:
            logger.exception(str(e))
            return []

    def call_geocode(self, housenumber: str, street: str, district: str = None,
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
                    results.append(SuggestionResult(
                        title=res['Location']['Address']['Label'],
                        vicinity=res['Location']['Address']['Label'],
                        position=[res['Location']['DisplayPosition']['Latitude'],
                                  res['Location']['DisplayPosition']['Longitude']]))
                return results
            else:
                return []
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
