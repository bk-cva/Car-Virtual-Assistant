from typing import List, Dict, Tuple

from .dialog_state_tracker import FeaturizedTracker
from ..nlu.intents.constants import Intent
from ..map.here import HereSDK
from .response_selector import ResponseSelector


class DialogManager:
    def __init__(self, selector: ResponseSelector):
        self.here_api = HereSDK()
        self.location_tracker = FeaturizedTracker(['place', 'place_name'])
        self.selector = selector

    def handle(self, intent: Intent, entities: List, **kwargs) -> Tuple[str, any]:
        # Reformat entities
        for i, entity in enumerate(entities):
            entities[i] = [entity.name, entity.value]

        latitude, longitude = kwargs.get('latitude'), kwargs.get('longitude')

        if intent == Intent.location:
            self.location_tracker.update_state(entities)

            if self.location_tracker.is_full:
                current_state = self.location_tracker.get_state()
                query = current_state['place'] + ' ' + current_state['place_name']
                items = self.here_api.call_autosuggest((latitude, longitude), query)
                item = self.selector.select(items)
                return 'res_loc', {'vicinity': item.vicinity}
        return '', None
