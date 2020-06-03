import json
import logging
import requests
from datetime import datetime

from ..common.config_manager import ConfigManager


logger = logging.getLogger(__name__)


class ScheduleSDK:
    def __init__(self):
        self.url = ConfigManager().get('CVA_DB_URL')
        self.calendar_id = ConfigManager().get('CALENDAR_ID')
        
    def request_schedule(self, time_min: datetime, time_max: datetime, q: str = None):
        try:
            time_min = time_min.astimezone().replace(microsecond=0).isoformat()
            time_max = time_max.astimezone().replace(microsecond=0).isoformat()
            payload = {'calendarId': self.calendar_id,
                       'timeMin': time_min,
                       'timeMax': time_max}
            if q is not None:
                payload['q'] = q
            logger.debug(json.dumps(payload))
            res = requests.get(self.url + '/calendar/event/query', params=payload)
            res.raise_for_status()
            return res.json()['items']
        except Exception as e:
            logger.exception(str(e))
            raise e
