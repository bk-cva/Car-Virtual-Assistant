import logging
from datetime import date
from unittest.mock import patch

from src.cva import CVA


fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
fh.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(fh)

mock_date_patcher = patch('src.dialog_manager.normalization.date')
mock_date = mock_date_patcher.start()
mock_date.today.return_value = date(2020, 5, 13)
mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

cva = CVA()
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

with open('snapshots/cva_snapshot.txt', mode='w', encoding='utf-8') as file:
    while True:
        if len(user_snapshot) == 0:
            break
        user_conversation = user_snapshot.pop(0)
        for utter in user_conversation:
            cva_response = cva(utter)[0][1]
            file.write(cva_response + '\n')
        file.write('\n')
        cva.manager.reset_state()

mock_date_patcher.stop()
