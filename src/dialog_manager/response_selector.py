from abc import ABCMeta, abstractmethod
from typing import List, TypeVar


T = TypeVar('T')


class ResponseSelector(metaclass=ABCMeta):
    @abstractmethod
    def select(self, items: List[T], **kwargs) -> T:
        pass


class FirstItemSelector(ResponseSelector):
    def select(self, items: List[T], **kwargs) -> T:
        return items[0]
