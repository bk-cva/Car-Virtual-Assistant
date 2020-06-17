import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple

from .dialog_state_tracker import FeaturizedTracker
from .response_selector import ResponseSelector
from .state import State
from .normalization import NormalEntity, normalize_date, normalize_time_range, normalize_time, normalize_duration
from src.nlu.intents.constants import Intent
from src.map.here import HereSDK
from src.utils import match_string, datetime_range_to_string, datetime_to_time_string
from src.db.schedule import ScheduleSDK


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DialogManager:
    def __init__(self, selector: ResponseSelector):
        self.here_api = HereSDK()
        self.schedule_api = ScheduleSDK()
        self.fsm = State.START
        self.main_intent = None
        self.cached = {}
        self.tracker = FeaturizedTracker(['place', 'place_property', 'route_property', 'info_type',
                                          'address', 'street', 'ward', 'district',
                                          'activity', 'event', 'number', 'date', 'time', 'duration'])
        self.selector = selector

    def reset_state(self):
        self._set_state(State.START)
        self._set_main_intent(None)
        self.cached = {}
        self.tracker.reset_state()

    def handle(self, intent: Intent, entities: List[NormalEntity], **kwargs) -> Tuple[str, any]:
        entities_list = [[entity.name, entity.value] for entity in entities] # Reformat entities

        if self.fsm == State.START:
            if intent == Intent.location:
                self._set_state(State.LOCATION)
            elif intent == Intent.path:
                self._set_state(State.ROUTE)
            elif intent == Intent.request_schedule:
                self._set_state(State.REQUEST_SCHEDULE)
            elif intent == Intent.create_schedule:
                self._set_state(State.CREATE_SCHEDULE)       
            elif intent == Intent.remind:
                self._set_state(State.CREATE_SCHEDULE)
            elif intent == Intent.cancel_schedule:
                self._set_state(State.CANCEL_SCHEDULE)
            else:
                return 'intent_not_found', {}

            self._set_main_intent(intent)

        elif self.fsm == State.LOCATION:
            self.tracker.reset_state()
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            if 'place' in current_state or 'activity' in current_state:
                self._set_state(State.FIND_LOCATION)
            elif 'street' in current_state:
                self._set_state(State.FIND_ADDRESS)
            else:
                self._set_state(State.FIND_CURRENT)

        elif self.fsm == State.FIND_LOCATION:
            items = self.execute(intent, entities, **kwargs)
            if len(items) > 0:
                self.cached['locations'] = items
                self._set_state(State.AUTO_SELECT)
            else:
                self._set_state(State.NO_LOCATION)
        
        elif self.fsm == State.FIND_ADDRESS:
            items = self.execute(intent, entities, **kwargs)
            if len(items) > 0:
                self._set_state(State.START)
                item = items[0]
                if self.main_intent == Intent.location:
                    return 'respond_address_location', vars(item)
                else:
                    routes = self.here_api.calculate_route((kwargs.get('latitude'),
                                                            kwargs.get('longitude')),
                                                           (item.latitude,
                                                            item.longitude))
                    return 'respond_address_path', vars(item)
            else:
                self._set_state(State.NO_LOCATION)
        
        elif self.fsm == State.FIND_CURRENT:
            latitude, longitude = kwargs.get(
                'latitude'), kwargs.get('longitude')
            items = self.execute(intent, entities, **kwargs)
            self._set_state(State.START)
            if len(items) > 0:
                return 'show_current_location', vars(items[0])
            else:
                return 'show_current_location_alt', {'latitude': latitude,
                                                     'longitude': longitude}

        elif self.fsm == State.NO_LOCATION:
            self._set_state(State.START)
            return 'no_location', {}
        
        elif self.fsm == State.AUTO_SELECT:
            items = self.cached['locations']
            if len(items) == 1:
                if self.main_intent == Intent.location:
                    self._set_state(State.RETURN_LOCATION)
                else:
                    self._set_state(State.FIND_ROUTE)
            else:
                query = self.cached['location_query']
                place_property = self.tracker.get_state('place_property')
                if place_property is not None:
                    if place_property == 'gần nhất':
                        index = min(enumerate(items), key=lambda x: x[1].distance)[0]
                        self.tracker.update_state([('number', index)])
                        if self.main_intent == Intent.location:
                            self._set_state(State.RETURN_LOCATION)
                        else:
                            self._set_state(State.FIND_ROUTE)
                else:
                    matched_items = []
                    for index, item in enumerate(items):
                        if match_string(query, item.title):
                            matched_items.append(index)
                    if len(matched_items) == 1:
                        self.tracker.update_state([('number', matched_items[0])])
                        if self.main_intent == Intent.location:
                            self._set_state(State.RETURN_LOCATION)
                        else:
                            self._set_state(State.FIND_ROUTE)
                    else:
                        self._set_state(State.SELECT_LOCATION)
                        return 'select_location', {'locations': self.cached['locations'],
                                                'num_locs': len(self.cached['locations'])}

        elif self.fsm == State.SELECT_LOCATION:
            if intent == Intent.select_item:
                self.tracker.update_state(entities_list)
                if self.main_intent == Intent.location:
                    self._set_state(State.RETURN_LOCATION)
                else:
                    self._set_state(State.FIND_ROUTE)
            else:
                self._set_state(State.START)

        elif self.fsm == State.RETURN_LOCATION:
            index = self.tracker.get_state('number', 0)
            item = self.cached['locations'][index]
            self._set_state(State.POST_RETURN_LOCATION)

            info_type = self.tracker.get_state('info_type')
            metadata = {'locations': [vars(item)]}
            if info_type is not None:
                if info_type == 'đường':
                    return 'respond_location_street', metadata
                elif info_type == 'quận':
                    return 'respond_location_district', metadata
                elif info_type == 'khoảng cách':
                    return 'respond_location_distance', metadata
            if len(self.cached['locations']) > 1:
                return 'respond_location', metadata
            else:
                return 'respond_location_single', metadata

        elif self.fsm == State.POST_RETURN_LOCATION:
            if intent == Intent.select_item:
                self._set_state(State.SELECT_LOCATION)
            elif intent == Intent.path:
                self._set_state(State.FIND_ROUTE)
            else:
                self._set_state(State.START)

        elif self.fsm == State.ROUTE:
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            if 'place' in current_state or 'activity' in current_state:
                self._set_state(State.FIND_LOCATION)
            elif 'street' in current_state:
                self._set_state(State.FIND_ADDRESS)
            else:
                self._set_state(State.ASK_PLACE)

        elif self.fsm == State.ASK_PLACE:
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            if 'place' in current_state:
                self._set_state(State.FIND_LOCATION)
            else:
                return 'ask_place', {}

        elif self.fsm == State.FIND_ROUTE:
            self._set_state(State.START)
            index = self.tracker.get_state('number', 0)
            destination = self.cached['locations'][index]
            routes = self.here_api.calculate_route((kwargs.get('latitude'),
                                                    kwargs.get('longitude')),
                                                   (destination.latitude,
                                                    destination.longitude))
            return 'respond_route', {
                'routes': routes,
                'locations': [destination],
                'title': destination.title}

        elif self.fsm == State.REQUEST_SCHEDULE:
            self.tracker.reset_state()
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            # Default is today
            time_min = datetime.combine(date.today(), datetime.min.time())
            time_max = time_min + timedelta(1)
            if 'date' in current_state:
                time_min = datetime.combine(normalize_date(
                    current_state['date']), datetime.min.time())
            if 'time' in current_state:
                time_from, time_to = normalize_time_range(
                    current_state['time'])
                time_max = time_min + timedelta(hours=time_to.hour,
                                                minutes=time_to.minute)
                time_min = time_min + timedelta(hours=time_from.hour,
                                                minutes=time_from.minute)
            else:
                time_max = time_min + timedelta(1)
            items = self.schedule_api.request_schedule(
                time_min=time_min, time_max=time_max)
            self._set_state(State.START)
            if len(items) > 0:
                return 'respond_request_schedule', {
                    'events': items,
                    'date_str': datetime_range_to_string(time_min, time_max)}
            else:
                return 'no_request_schedule', {
                    'date_str': datetime_range_to_string(time_min, time_max)}

        elif self.fsm == State.CREATE_SCHEDULE:
            self.tracker.reset_state()
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            if 'event' in current_state or 'activity' in current_state:
                if 'time' in current_state:
                    if self.main_intent == Intent.create_schedule:
                        self._set_state(State.ASK_DURATION)
                        return 'ask_duration', {}
                    self._set_state(State.CALL_CREATE_SCHEDULE)
                    return None
                self._set_state(State.ASK_TIME)
                return 'ask_time', {}
            self._set_state(State.ASK_EVENT)
            return 'ask_event', {}

        elif self.fsm == State.ASK_EVENT:
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            if 'event' in current_state or 'activity' in current_state:
                if 'time' in current_state:
                    if self.main_intent == Intent.create_schedule:
                        self._set_state(State.ASK_DURATION)
                        return 'ask_duration', {}
                    self._set_state(State.CALL_CREATE_SCHEDULE)
                    return None
                self._set_state(State.ASK_TIME)
                return 'ask_time', {}
            else:
                self._set_state(State.START)

        elif self.fsm == State.ASK_TIME:
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            if 'time' in current_state:
                if self.main_intent == Intent.create_schedule:
                    self._set_state(State.ASK_DURATION)
                    return 'ask_duration', {}
                self._set_state(State.CALL_CREATE_SCHEDULE)
                return None
            else:
                self._set_state(State.START)

        elif self.fsm == State.ASK_DURATION:
            try:
                time_entities = next(e for e in entities_list if e[0] == 'time')
                self.tracker.update_state([('duration', time_entities[1])])
                self._set_state(State.CALL_CREATE_SCHEDULE)
            except StopIteration:
                self._set_state(State.START)

        elif self.fsm == State.CALL_CREATE_SCHEDULE:
            current_state = self.tracker.get_state()
            # Default is today
            start_time = datetime.combine(date.today(), datetime.min.time())
            if 'date' in current_state:
                start_time = datetime.combine(
                    normalize_date(current_state['date']), datetime.min.time())
            time_from = normalize_time(current_state['time'])
            start_time = start_time + timedelta(hours=time_from.hour,
                                                minutes=time_from.minute)
            # If main_intent is remind, set default end time to 5 minutes later.
            end_time = start_time + timedelta(minutes=5)
            if 'duration' in current_state:
                duration = normalize_duration(current_state['duration'])
                end_time = start_time + duration
            summary = current_state.get('event', current_state.get('activity'))
            try:
                self.schedule_api.create_schedule(
                    summary=summary,
                    start_time=start_time,
                    end_time=end_time)
                self._set_state(State.START)
                return 'respond_create_schedule', {
                    'summary': summary,
                    'time_str': datetime_to_time_string(start_time)}
            except Exception:
                self._set_state(State.START)
                return 'respond_create_schedule_alt', {}

        elif self.fsm == State.CANCEL_SCHEDULE:
            self.tracker.reset_state()
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            # Default is today
            time_min = datetime.combine(date.today(), datetime.min.time())
            time_max = time_min + timedelta(1)
            if 'date' in current_state:
                time_min = datetime.combine(normalize_date(
                    current_state['date']), datetime.min.time())
            if 'time' in current_state:
                time_from, time_to = normalize_time_range(
                    current_state['time'])
                time_max = time_min + timedelta(hours=time_to.hour,
                                                minutes=time_to.minute)
                time_min = time_min + timedelta(hours=time_from.hour,
                                                minutes=time_from.minute)
            else:
                time_max = time_min + timedelta(1)
            items = self.schedule_api.request_schedule(
                time_min=time_min, time_max=time_max)
            self.cached['schedules'] = items
            if len(items) == 0:
                self._set_state(State.NO_SCHEDULE)
            elif len(items) == 1:
                self._set_state(State.ASK_CANCEL)
                return 'ask_cancel', {'schedule': items[0]}
            else:
                self._set_state(State.SELECT_SCHEDULE)
                return 'select_schedule', {'schedules': items}

        elif self.fsm == State.NO_SCHEDULE:
            return 'no_schedule', {}

        elif self.fsm == State.SELECT_SCHEDULE:
            if intent == Intent.select_item:
                self.tracker.update_state(entities_list)
                self._set_state(State.ASK_CANCEL)
                return 'ask_cancel', {'schedule': self.cached['schedules'][self.tracker.get_state('number')]}
            else:
                self._set_state(State.START)

        elif self.fsm == State.ASK_CANCEL:
            if intent == Intent.yes:
                self._set_state(State.CALL_CANCEL_SCHEDULE)
            elif intent == Intent.no:
                self._set_state(State.ABORT_CANCEL)
            else:
                self._set_state(State.START)

        elif self.fsm == State.ABORT_CANCEL:
            return 'abort_cancel', {}

        elif self.fsm == State.CALL_CANCEL_SCHEDULE:
            schedule = self.cached['schedules'][self.tracker.get_state('number', 0)]
            try:
                self.schedule_api.cancel_schedule(schedule.id)
                self._set_state(State.START)
                return 'respond_cancel_schedule', {}
            except Exception:
                self._set_state(State.START)
                return 'respond_cancel_schedule_alt', {}

        else:
            raise Exception('Unexpected state {}'.format(self.fsm))

        return None

    def execute(self, intent: Intent, entities: List, **kwargs) -> Tuple[str, any]:
        current_state = self.tracker.get_state()
        if self.fsm == State.FIND_LOCATION:
            query = current_state.get('place', current_state.get('activity'))
            if 'street' in current_state:
                query += ' đường ' + current_state['street']
            if 'district' in current_state:
                query += ' quận ' + current_state['district']
            latitude, longitude = kwargs.get(
                'latitude'), kwargs.get('longitude')
            self.cached['location_query'] = query
            items = self.here_api.search((latitude, longitude), query)
            return items

        elif self.fsm == State.FIND_ADDRESS:
            latitude, longitude = kwargs.get(
                'latitude'), kwargs.get('longitude')
            query = {'street': current_state.get('street')}
            if 'address' in current_state:
                query['housenumber'] = current_state.get('address')
            if 'district' in current_state:
                query['district'] = current_state.get('district')
            items = self.here_api.geocode((latitude, longitude), **query)
            return items
        
        elif self.fsm == State.FIND_CURRENT:
            latitude, longitude = kwargs.get(
                'latitude'), kwargs.get('longitude')
            items = self.here_api.reverse_geocode(latitude, longitude)
            return items

    def _set_state(self, state: State):
        logger.debug('Change state: {} -> {}'.format(self.fsm.name, state.name))
        self.fsm = state
    

    def _set_main_intent(self, intent: Intent):
        self.main_intent = intent
