from datetime import datetime

class Time:
    def __init__(self, dateTime: str):
        dateTime = dateTime[:19] # remove time zone
        self.dateTime = datetime.strptime(dateTime, '%Y-%m-%dT%H:%M:%S')
