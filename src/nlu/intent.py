from enum import Enum


class Intent(str, Enum):
    path = 'path'
    location = 'location'
    music = 'music'
    remind = 'remind'
    control_door = 'control_door'
    control_window = 'control_window'
    control_aircon = 'control_aircon'
    control_radio = 'control_radio'
    request_schedule = 'request_schedule'
    create_schedule = 'create_schedule'
    cancel_schedule = 'cancel_schedule'
    request_news = 'request_news'
    phone_call = 'phone_call'
    phone_text = 'phone_text'
    select_item = 'select_item'
    yes = 'yes'
    no = 'no'
