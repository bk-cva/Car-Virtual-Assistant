from os import getenv
from dotenv import load_dotenv

from src.singleton import Singleton


class ConfigManager(metaclass=Singleton):
    def __init__(self):
        load_dotenv()

    @staticmethod
    def get(key: str, default=None):
        return getenv(key, default)
