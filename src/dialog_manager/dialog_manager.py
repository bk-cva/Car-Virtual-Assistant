import logging
from typing import List, Dict, Tuple

from .dialog_state_tracker import FeaturizedTracker
from ..nlu.intents.constants import Intent
from ..map.here import HereSDK
from .response_selector import ResponseSelector
from .state import State


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DialogManager:
    def __init__(self, selector: ResponseSelector):
        self.here_api = HereSDK()
        self.fsm = State.START
        self.cached = {}
        self.location_tracker = FeaturizedTracker(['place', 'place_property', 'info_type',
                                                   'address', 'street', 'ward', 'district',
                                                   'activity'])
        self.path_tracker = FeaturizedTracker(['place', 'info_type'])
        self.selector = selector

    def handle(self, intent: Intent, entities: List, **kwargs) -> Tuple[str, any]:
        entities_list = [[entity.name, entity.value] for entity in entities] # Reformat entities

        if self.fsm == State.START:
            if intent == Intent.location:
                self._set_state(State.LOCATION)
            
            if intent == Intent.create_schedule:
                pass
        
        elif self.fsm == State.LOCATION:
            self.location_tracker.reset_state()
            self.location_tracker.update_state(entities_list)
            current_state = self.location_tracker.get_state()
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
                if len(items) > 1:
                    self._set_state(State.SELECT_LOCATION)
                else:
                    self._set_state(State.RETURN_LOCATION)
            else:
                self._set_state(State.NO_LOCATION)
        
        elif self.fsm == State.FIND_ADDRESS:
            items = self.execute(intent, entities, **kwargs)
            if len(items) > 0:
                self.cached['locations'] = items
                self._set_state(State.RETURN_LOCATION)
            else:
                self._set_state(State.NO_LOCATION)
        
        elif self.fsm == State.FIND_CURRENT:
            latitude, longitude = kwargs.get(
                'latitude'), kwargs.get('longitude')
            items = self.execute(intent, entities, **kwargs)
            self._set_state(State.START)
            if len(items) > 0:
                return 'show_current_location', {'address': items[0].vicinity,
                                                 'latitude': latitude,
                                                 'longitude': longitude}
            else:
                return 'show_current_location_alt', {'latitude': latitude,
                                                     'longitude': longitude}

        elif self.fsm == State.NO_LOCATION:
            self._set_state(State.START)
            return 'no_location', {}

        elif self.fsm == State.SELECT_LOCATION:
            if intent == Intent.select_item:
                self.cached['selected_location'] = list(filter(lambda x: x.name == 'number', entities))[0].value
                self._set_state(State.RETURN_LOCATION)
            else:
                return 'select_location', {'locations': self.cached['locations'],
                                           'num_locs': len(self.cached['locations'])}

        elif self.fsm == State.RETURN_LOCATION:
            self._set_state(State.START)
            index = self.cached.get('selected_location', 0)
            item = self.cached['locations'][index]
            return 'respond_location', {'address': item.vicinity,
                                        'latitude': item.position[0],
                                        'longitude': item.position[1]}
        else:
            raise Exception('Unexpected state {}'.format(self.fsm))

        return None

    def execute(self, intent: Intent, entities: List, **kwargs) -> Tuple[str, any]:
        if self.fsm == State.FIND_LOCATION:
            current_state = self.location_tracker.get_state()
            query = current_state.get('place', current_state.get('activity'))
            if 'street' in current_state:
                query += ' đường ' + current_state['street']
            if 'district' in current_state:
                query += ' quận ' + current_state['district']
            latitude, longitude = kwargs.get(
                'latitude'), kwargs.get('longitude')
            items = self.here_api.call_autosuggest((latitude, longitude), query)
            return items

        elif self.fsm == State.FIND_ADDRESS:
            current_state = self.location_tracker.get_state()
            query = {'street': current_state.get('street')}
            if 'address' in current_state:
                query['housenumber'] = current_state.get('address')
            if 'district' in current_state:
                query['district'] = current_state.get('district')
            items = self.here_api.call_geocode(**query)
            return items
        
        elif self.fsm == State.FIND_CURRENT:
            latitude, longitude = kwargs.get(
                'latitude'), kwargs.get('longitude')
            items = self.here_api.call_reverse_geocode(latitude, longitude)
            return items

    def _set_state(self, state: State):
        logger.debug('Change state: {} -> {}'.format(self.fsm.name, state.name))
        self.fsm = state
