from typing import List, Dict, Tuple

from .dialog_state_tracker import FeaturizedTracker
from ..nlu.intents.constants import Intent
from ..map.here import HereSDK
from .response_selector import ResponseSelector


class DialogManager:
    def __init__(self, selector: ResponseSelector):
        self.here_api = HereSDK()
        self.location_tracker = FeaturizedTracker(['place', 'personal_place', 'place_property', 'info_type',
                                                   'address', 'street', 'ward', 'district'])
        self.path_tracker = FeaturizedTracker(['place', 'info_type'])
        self.selector = selector

    def handle(self, intent: Intent, entities: List, **kwargs) -> Tuple[str, any]:
        # Reformat entities
        for i, entity in enumerate(entities):
            entities[i] = [entity.name, entity.value]

        latitude, longitude = kwargs.get('latitude'), kwargs.get('longitude')

        if intent == Intent.location:
            self.location_tracker.update_state(entities)
            current_state = self.location_tracker.get_state()
            if 'place' in current_state:
                query = current_state['place']
                items = self.here_api.call_autosuggest((latitude, longitude), query)
                item = self.selector.select(items)
                return_dict = {'address': item.vicinity}
                return 'res_loc', return_dict
            elif 'personal_place' in current_state:
                pass
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
                        return 'res_loc', {'address': result['Location']['Address']['Label'],
                                           'latitude': result['Location']['DisplayPosition']['Latitude'],
                                           'longitude': result['Location']['DisplayPosition']['Longitude']}
                return 'no_loc', None

        # elif intent == Intent.path:
        #     self.path_tracker.update_state(entities)
        #     current_state = self.path_tracker.get_state()
        #     if 'place' in current_state:

        return '', None
