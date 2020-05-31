import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from .dialog_state_tracker import FeaturizedTracker
from .response_selector import ResponseSelector
from .state import State
from .normalization import NormalEntity
from src.nlu.intents.constants import Intent
from src.map.here import HereSDK
from src.utils import match_string, datetime_range_to_string
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
                                          'activity', 'event', 'number', 'date', 'time'])
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
                self._set_main_intent(Intent.location)

            elif intent == Intent.request_schedule:
                self._set_state(State.REQUEST_SCHEDULE)
                self._set_main_intent(Intent.request_schedule)
            
            elif intent == Intent.path:
                self._set_state(State.ROUTE)
                self._set_main_intent(Intent.path)
            
            else:
                return 'intent_not_found', {}
        
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
                return 'respond_address', vars(items[0])
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
                        print([(item.title, item.distance) for item in items])
                        index = min(enumerate(items), key=lambda x: x[1].distance)[0]
                        print(index)
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
            if info_type is not None:
                if info_type == 'đường':
                    return 'respond_location_street', vars(item)
                elif info_type == 'quận':
                    return 'respond_location_district', vars(item)
                elif info_type == 'khoảng cách':
                    return 'respond_location_distance', vars(item)
            if len(self.cached['locations']) > 1:
                return 'respond_location', vars(item)
            else:
                return 'respond_location_single', vars(item)

        elif self.fsm == State.POST_RETURN_LOCATION:
            if intent == Intent.select_item:
                self._set_state(State.SELECT_LOCATION)
            elif intent == Intent.path:
                self._set_state(State.FIND_ROUTE)
            else:
                self._set_state(State.START)

        elif self.fsm == State.REQUEST_SCHEDULE:
            self.tracker.reset_state()
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            if 'time' in current_state or 'date' in current_state:
                self._set_state(State.REQUESTING_SCHEDULE)
            else:
                self._set_state(State.ASK_DATE_TIME)

        elif self.fsm == State.ASK_DATE_TIME:
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            if 'time' in current_state or 'date' in current_state:
                self._set_state(State.REQUESTING_SCHEDULE)
            else:
                return 'ask_date_time', {}

        elif self.fsm == State.REQUESTING_SCHEDULE:
            items = self.execute(intent, entities, **kwargs)
            current_state = self.tracker.get_state()
            self._set_state(State.START)
            if len(items) > 0:
                return 'respond_request_schedule', {'datetime': datetime_range_to_string(self.cached['request_schedule_time_min'], self.cached['request_schedule_time_max']),
                                                    'events': items,
                                                    'num_events': len(items),
                                                    'list': ', '.join(map(lambda x: x['summary'], items))}
            else:
                return 'no_request_schedule', {'datetime': datetime_range_to_string(self.cached['request_schedule_time_min'], self.cached['request_schedule_time_max'])}

        elif self.fsm == State.ROUTE:
            self.tracker.update_state(entities_list)
            current_state = self.tracker.get_state()
            if 'place' in current_state:
                self._set_state(State.FIND_LOCATION)
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
            return 'respond_route', {'routes': routes, 'title': destination.title}

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
            query = {'street': current_state.get('street')}
            if 'address' in current_state:
                query['housenumber'] = current_state.get('address')
            if 'district' in current_state:
                query['district'] = current_state.get('district')
            items = self.here_api.geocode(**query)
            return items
        
        elif self.fsm == State.FIND_CURRENT:
            latitude, longitude = kwargs.get(
                'latitude'), kwargs.get('longitude')
            items = self.here_api.reverse_geocode(latitude, longitude)
            return items
        
        elif self.fsm == State.REQUESTING_SCHEDULE:
            timeMin = datetime.now()
            timeMax = datetime.now() + timedelta(1)
            if 'date' in current_state:
                minDate = datetime.combine(current_state['date'], datetime.min.time())
                maxDate = minDate + timedelta(1)
                self.cached['request_schedule_time_min'] = minDate
                self.cached['request_schedule_time_max'] = maxDate
                timeMin = minDate.astimezone().replace(microsecond=0).isoformat()
                timeMax = maxDate.astimezone().replace(microsecond=0).isoformat()
            items = self.schedule_api.request_schedule(timeMin=timeMin, timeMax=timeMax)
            return items

    def _set_state(self, state: State):
        logger.debug('Change state: {} -> {}'.format(self.fsm.name, state.name))
        self.fsm = state
    

    def _set_main_intent(self, intent: Intent):
        self.main_intent = intent
