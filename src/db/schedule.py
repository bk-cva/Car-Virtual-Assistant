import json
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import List

from ..config_manager import ConfigManager
from .entities.event import Event


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
tz = timezone(timedelta(hours=7))

def datetime2str(d: datetime) -> str:
    return d.astimezone().replace(microsecond=0, tzinfo=tz).isoformat()


class ScheduleSDK:
    def __init__(self):
        config = ConfigManager()
        self.url = config.get('CVA_DB_URL')
        self.calendar_id = config.get('CALENDAR_ID')
        self.dry_run = config.get('SCHEDULE_API_DRY_RUN') == 'true'

    def request_schedule(self, time_min: datetime, time_max: datetime, q: str = None) -> List[Event]:
        try:
            payload = {'calendarId': self.calendar_id,
                       'timeMin': datetime2str(time_min),
                       'timeMax': datetime2str(time_max)}
            if q is not None:
                payload['q'] = q
            logger.debug(json.dumps(payload))
            res = requests.get(self.url + '/calendar/event/query', params=payload)
            res.raise_for_status()
            events = [Event(**item, _id=item['id']) for item in res.json()['items']]
            return events
        except Exception as e:
            logger.exception(str(e))
            raise e

    def create_schedule(self,
                        summary: str,
                        start_time: datetime,
                        end_time: datetime = None,
                        location: str = None):
        try:
            payload = {'calendarId': self.calendar_id,
                       'summary': summary,
                       'start': datetime2str(start_time)}
            if end_time is not None:
                payload['end'] = datetime2str(end_time)
            if location is not None:
                payload['location'] = location
            logger.info(json.dumps(payload))
            if not self.dry_run:
                res = requests.post(self.url + '/calendar/event', json=payload)
                res.raise_for_status()
                return res.json()
        except Exception as e:
            logger.exception(str(e))
            raise e

    def cancel_schedule(self,
                        event_id: str):
        try:
            payload = {'calendarId': self.calendar_id,
                       'eventId': event_id}
            logger.info(json.dumps(payload))
            if not self.dry_run:
                res = requests.delete(self.url + '/calendar/event', json=payload)
                res.raise_for_status()
        except Exception as e:
            logger.exception(str(e))
            raise e
