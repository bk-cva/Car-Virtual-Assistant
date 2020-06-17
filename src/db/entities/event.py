from typing import Dict

from .time import Time
from .creator import Creator

class Event:
    def __init__(self,
                 _id: str,
                 summary: str,
                 start: Dict,
                 end: Dict,
                 kind: str = None,
                 status: str = None,
                 created: str = None,
                 updated: str = None,
                 creator: Dict = None,
                 organizer: Dict = None,
                 reminders: any = None,
                 **kwargs):
        self.id = _id
        self.summary = summary
        self.start = Time(start['dateTime'])
        self.end = Time(end['dateTime'])
        self.kind = kind
        self.status = status
        self.created = created
        self.updated = updated
        if creator:
            self.creator = Creator(creator.get('email'))
        if organizer:
            self.organizer = Creator(organizer.get('email'))
        self.reminders = reminders

