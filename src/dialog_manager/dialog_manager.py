from typing import List, Dict, Tuple

from .dialog_state_tracker import FeaturizedTracker
from ..nlu.intents.constants import Intent
from ..map.here import HereSDK
from .response_selector import ResponseSelector
from .state import State


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
        latitude, longitude = kwargs.get('latitude'), kwargs.get('longitude')

        if self.fsm == State.START:
            if intent == Intent.location:
                self._set_state(State.FIND_LOCATION)
                self.location_tracker.update_state(entities_list)
                current_state = self.location_tracker.get_state()
                if 'place' in current_state:
                    query = current_state['place']
                    items = self.here_api.call_autosuggest(
                        (latitude, longitude), query)
                    if len(items) > 0:
                        item = self.selector.select(items)
                        return 'respond_location', {'address': item.vicinity,
                                                    'latitude': item.position[0],
                                                    'longitude': item.position[1]}
                    return 'no_location', None
                elif 'street' in current_state:
                    query = {'street': current_state.get('street')}
                    if 'address' in current_state:
                        query['housenumber'] = current_state.get('address')
                    if 'district' in current_state:
                        query['district'] = current_state.get('district')
                    items = self.here_api.call_geocode(**query)
                    if len(items) > 0:
                        if len(items[0]['Result']) > 0:
                            result = items[0]['Result'][0]
                            return 'respond_location', {'address': result['Location']['Address']['Label'],
                                                        'latitude': result['Location']['DisplayPosition']['Latitude'],
                                                        'longitude': result['Location']['DisplayPosition']['Longitude']}
                    return 'no_loc', None
                elif 'activity' in current_state:
                    query = current_state['activity']
                    items = self.here_api.call_autosuggest(
                        (latitude, longitude), query)
                    if len(items) > 0:
                        if len(items) > 1:
                            self.cached['locations'] = items
                            return 'select_location', {'locations': items, 'num_locs': len(items)}
                        else:
                            return 'respond_location', {'address': item[0].vicinity}
                    return 'no_location', None
                else:
                    return 'show_location', {'location': 'hiện tại',
                                            'latitude': latitude,
                                            'longitude': longitude}

        elif self.fsm == State.FIND_LOCATION:
            if intent == Intent.select_item:
                self._set_state(State.SELECT_LOCATION)
                item = self.cached['locations'][int(
                    list(filter(lambda x: x.name == 'number', entities))[0].value) - 1]
                return 'respond_location', {'address': item.vicinity,
                                            'latitude': item.position[0],
                                            'longitude': item.position[1]}
        elif self.fsm == State.SELECT_LOCATION:
            if intent == Intent.path:
                pass
        else:
            raise Exception('Unexpected state {}'.format(self.fsm))

        return '', None

    def _set_state(self, state: State):
        self.fsm = state
