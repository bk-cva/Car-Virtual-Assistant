import requests
import logging
from requests.exceptions import HTTPError
from typing import Tuple, List


from .entities import SuggestionResult


class HereSDK:
    def __init__(self, api_key):
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
            response = requests.get('https://places.sit.ls.hereapi.com/places/v1/autosuggest', params={
                'apiKey': self.api_key,
                'at': ','.join(map(str, at)),
                'q': q
            })
            response.raise_for_status()
            results = []
            for res in response.json()['results']:
                results.append(SuggestionResult(**res))
            return results
        except HTTPError as e:
            logging.error(e)
            return []
