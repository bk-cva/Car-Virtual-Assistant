from os import getenv
from dotenv import load_dotenv

from src.singleton import Singleton
from .config_schema import ConfigSchema


class ConfigManager(metaclass=Singleton):
    def __init__(self):
        load_dotenv()
        self.config = ConfigSchema(
            here_api_key=getenv('HERE_API_KEY'),
            nlu_url=getenv('NLU_URL'),
            cva_db_url=getenv('CVA_DB_URL'),
            calendar_id=getenv('CALENDAR_ID'),
            do_call_external_nlu=getenv('DO_CALL_EXTERNAL_NLU'),
            schedule_api_dry_run=getenv('SCHEDULE_API_DRY_RUN'),
            timezone=getenv('TIMEZONE', '+07:00'),
        )

    def get(self, key: str):
        return vars(self.config).get(key.lower())
