import re
import logging
import os.path
from datetime import datetime
from typing import Dict


from ..utils.func import datetime_to_time_string


logger = logging.getLogger(__name__)


class NLG:
    def __init__(self):
        self.html_tag = re.compile(r'<[^>]+>')
        self.newline = re.compile(r'\\n|\\t|\\b|\\r')
        self.dup_space = re.compile(r'\s+')

    def __call__(self, action: str, substitutes: Dict) -> str:
        if action == 'intent_not_found':
            response = 'Xin lỗi, tôi không hiểu ý bạn.'

        elif action.startswith('respond_location'):
            location = substitutes['locations'][0]
            if action.endswith('single'):
                response = 'Tôi tìm được 1 địa điểm là {title}.'.format(**location)
            elif action.endswith('street'):
                response = 'Nó nằm trên đường {street}.'.format(**location)
            elif action.endswith('district'):
                response = 'Nó nằm ở {district}.'.format(**location)
            elif action.endswith('distance'):
                response = 'Cách đây {distance} mét.'.format(**location)
            else:
                response = 'Địa điểm bạn muốn tìm là {title}.'.format(**location)

        elif action == 'respond_address_location':
            address = []
            if 'houseNumber' in substitutes:
                address.append('số {}'.format(substitutes['houseNumber']))
            if 'street' in substitutes:
                address.append('đường {}'.format(substitutes['street']))
            response = 'Vị trí của {} đang hiển thị trên bản đồ.'.format(' '.join(address))

        elif action == 'respond_address_path':
            address = []
            if 'houseNumber' in substitutes:
                address.append('số {}'.format(substitutes['houseNumber']))
            if 'street' in substitutes:
                address.append('đường {}'.format(substitutes['street']))
            response = 'Đường đến {} đang hiển thị trên bản đồ.'.format(' '.join(address))

        elif action == 'show_current_location':
            response = 'Bạn đang ở gần {houseNumber} đường {street} {district} {city}.'.format(**substitutes)

        elif action == 'show_current_location_alt':
            response = 'Không tìm được địa chỉ nào quanh đây. Vị trí hiện tại của bạn đang được hiển thị.'.format(**substitutes)

        elif action == 'select_location':
            response = 'Tôi tìm được {num_locs} địa điểm liên quan.'.format(**substitutes)

        elif action == 'no_location':
            response = 'Không tìm thấy địa điểm.'.format(**substitutes)

        elif action == 'respond_request_schedule' or action == 'no_request_schedule':
            if action == 'respond_request_schedule':
                response = 'Có {} sự kiện'.format(
                    len(substitutes['events']))
            else:
                response = 'Không có sự kiện'.format(**substitutes)
            
            time_min = substitutes['time_min']
            time_max = substitutes['time_max']
            if time_min.time() == datetime.min.time() and time_max.time() == datetime.min.time():
                response += ' trong ' + time_min.strftime('ngày %d tháng %m')
            else:
                response += ' từ ' + datetime_to_time_string(time_min) + ' đến ' + datetime_to_time_string(time_max)
            response += '.'

        elif action == 'ask_time':
            response = 'Trong thời gian nào?'

        elif action == 'ask_event':
            response = 'Bạn muốn đặt tên sự kiện này là gì?'

        elif action == 'ask_duration':
            response = 'Trong bao lâu?'

        elif action == 'respond_create_schedule':
            response = 'Xong. {} lúc {} đã được tạo.'.format(
                substitutes['summary'],
                datetime_to_time_string(substitutes['start_time']))

        elif action == 'respond_create_schedule_alt':
            response = 'Có vẻ như việc tạo lịch không thành công. Hãy thử lại sau nhé!'

        elif action == 'respond_route':
            response = 'Tôi đã tìm được đường đến {title}.'.format(**substitutes)

        elif action == 'ask_place':
            response = 'Bạn muốn đi đâu?'.format(**substitutes)

        elif action == 'no_schedule':
            response = 'Tôi không tìm được sự kiện nào như thế trong lịch.'

        elif action == 'select_schedule':
            response = 'Tôi tìm được {} sự kiện. Bạn hãy chọn sự kiện mà bạn muốn hủy.'.format(
                len(substitutes['events']))

        elif action == 'ask_cancel':
            event = substitutes['events'][0]
            response = 'Bạn có chắc muốn hủy sự kiện {} diễn ra vào lúc {} không?'.format(
                event.summary,
                datetime_to_time_string(event.start.dateTime))

        elif action == 'abort_cancel':
            response = 'OK, lịch của bạn vẫn được giữ nguyên.'

        elif action == 'respond_cancel_schedule':
            response = 'Đã hủy sự kiện.'

        elif action == 'respond_cancel_schedule_alt':
            response = 'Đã có lỗi xảy ra. Có thể là do mạng không ổn định. Bạn hãy thử lại sau nhé.'

        elif action == 'respond_control_aircon':
            action_type = 'bật' if substitutes['action_type'] == 1 else 'tắt'
            response = 'Điều hòa đã được {}'.format(action_type)

        elif action == 'respond_control_door':
            action_type = 'mở' if substitutes['action_type'] == 1 else 'đóng'
            response = 'Cửa đã được {}'.format(action_type)

        elif action == 'respond_control_window':
            action_type = 'mở' if substitutes['action_type'] == 1 else 'đóng'
            response = 'Cửa sổ đã được {}'.format(action_type)

        elif action == 'respond_control_radio':
            action_type = 'bật' if substitutes['action_type'] == 1 else 'tắt'
            response = 'Đài {} đã được {}'.format(
                substitutes['radio_channel'], action_type)

        elif action == 'ask_song':
            response = 'Bạn muốn nghe bài gì?'

        elif action == 'respond_music':
            response = 'Bài mà bạn yêu cầu đã có. Chúc bạn nghe nhạc vui vẻ :D!'

        else:
            logger.warning('No template found for \'{}\', use default.'.format(action))
            return action, 'Đã xảy ra lỗi.'

        return action, self._clean(response)

    def _clean(self, text):
        text = self.html_tag.sub(' ', text)
        text = self.newline.sub(' ', text)
        text = self.dup_space.sub(' ', text)
        return text.strip()


