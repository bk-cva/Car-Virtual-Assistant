import os

os.environ['SCHEDULE_API_DRY_RUN'] = 'true'

import logging
from datetime import date, datetime
from unittest.mock import patch

from src.cva import CVA
from src.config_manager import ConfigManager


fh = logging.FileHandler('debug-snapshot.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
fh.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(fh)

mock_date_patcher = patch('src.dialog_manager.normalization.date')
mock_date = mock_date_patcher.start()
mock_date.today.return_value = date(2020, 5, 13)
mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

mock_now_patcher = patch('src.dialog_manager.normalization.now')
mock_now = mock_now_patcher.start()
mock_now.return_value = datetime(2020, 5, 13, 7, 0, 0)


do_call_external_nlu = ConfigManager().get('DO_CALL_EXTERNAL_NLU') == 'true'
cva = CVA(do_call_external_nlu=do_call_external_nlu)

user_snapshot = []
with open('snapshots/user_snapshot.txt', mode='r', encoding='utf-8') as file:
    user_conversation = []
    while True:
        line = file.readline()
        if not line:
            if len(user_conversation) > 0:
                user_snapshot.append(user_conversation)
            break
        if len(line.strip()) > 0:
            user_conversation.append(line)
        else:
            user_snapshot.append(user_conversation)
            user_conversation = []

with open('snapshots/conversation_snapshot.txt', mode='w', encoding='utf-8') as file:
    while True:
        if len(user_snapshot) == 0:
            break
        user_conversation = user_snapshot.pop(0)
        for utter in user_conversation:
            utter = utter.strip()
            cva_response = cva(utter)[0][1]
            file.write('User: {}\n'.format(utter))
            file.write('CVA: {}\n'.format(cva_response))
        file.write('\n')
        cva.manager.reset_state()

mock_date_patcher.stop()
