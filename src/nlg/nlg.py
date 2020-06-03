import re
import logging
import os.path
from typing import Dict


logger = logging.getLogger(__name__)


class NLG:
    def __init__(self):
        self.html_tag = re.compile(r'<[^>]+>')
        self.newline = re.compile(r'\\n|\\t|\\b|\\r')
        self.dup_space = re.compile(r'\s+')

    def __call__(self, action, substitutes: Dict) -> str:
        # preprocess substitutes
        for k, v in substitutes.items():
            if v is None:
                substitutes[k] = ''
        if 'street' in substitutes:
            substitutes['street'] = re.sub(r'^đường', '', substitutes['street'], flags=re.IGNORECASE)

        if action == 'intent_not_found':
            response = 'Xin lỗi, tôi không hiểu ý bạn.'

        elif action == 'respond_location':
            response = 'Địa điểm bạn muốn tìm là {title}.'.format(**substitutes)

        elif action == 'respond_location_single':
            response = 'Tôi tìm được 1 địa điểm là {title}.'.format(**substitutes)

        elif action == 'respond_location_street':
            response = 'Nó nằm trên đường {street}.'.format(**substitutes)

        elif action == 'respond_location_district':
            response = 'Nó nằm ở {district}.'.format(**substitutes)

        elif action == 'respond_location_distance':
            response = 'Cách đây {distance} mét.'.format(**substitutes)

        elif action == 'respond_address_location':
            response = 'Vị trí cần tìm đang hiển thị trên bản đồ.'.format(**substitutes)

        elif action == 'respond_address_path':
            response = 'Đường đến vị trí cần tìm đang hiển thị trên bản đồ.'.format(**substitutes)

        elif action == 'show_current_location':
            response = 'Bạn đang ở gần {houseNumber} đường {street} {district} {city}.'.format(**substitutes)

        elif action == 'show_current_location_alt':
            response = 'Không tìm được địa chỉ nào quanh đây. Vị trí hiện tại của bạn đang được hiển thị.'.format(**substitutes)

        elif action == 'select_location':
            response = 'Tôi tìm được {num_locs} địa điểm liên quan.'.format(**substitutes)

        elif action == 'no_location':
            response = 'Không tìm thấy địa điểm.'.format(**substitutes)

        elif action == 'respond_request_schedule':
            response = 'Có {num_events} sự kiện sẽ diễn ra vào {datetime}.'.format(**substitutes)

        elif action == 'no_request_schedule':
            response = '{datetime} không có sự kiện.'.format(**substitutes)

        elif action == 'ask_date_time':
            response = 'Trong thời gian nào?'.format(**substitutes)

        elif action == 'respond_route':
            response = 'Tôi đã tìm được đường đến {title}.'.format(**substitutes)

        elif action == 'ask_place':
            response = 'Bạn muốn đi đâu?'.format(**substitutes)

        else:
            logger.warning('No template found for \'{}\', use default.'.format(action))
            return action, 'Đã xảy ra lỗi.'

        return action, self._clean(response)

    def _clean(self, text):
        text = self.html_tag.sub(' ', text)
        text = self.newline.sub(' ', text)
        text = self.dup_space.sub(' ', text)
        return text.strip()


