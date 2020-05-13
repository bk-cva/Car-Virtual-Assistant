import logging
import requests

from ..common.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class ScheduleSDK:
    def __init__(self):
        self.url = ConfigManager().get('CVA_DB_URL')
        self.calendar_id = ConfigManager().get('CALENDAR_ID')
        
    def request_schedule(self, timeMin: str, timeMax: str, q: str = None):
        try:
            payload = {'calendarId': self.calendar_id,
                       'timeMin': timeMin,
                       'timeMax': timeMax}
            if q is not None:
                payload['q'] = q
            res = requests.get(self.url + '/calendar/event/query', params=payload)
            res.raise_for_status()
            return res.json()['items']
        except Exception as e:
            logger.exception(str(e))
            raise e
