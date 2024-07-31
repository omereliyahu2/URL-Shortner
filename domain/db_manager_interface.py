from abc import ABC, abstractmethod
from typing import Any


class DBManagerInterface(ABC):
    @abstractmethod
    def add(self, obj: Any):
        raise NotImplementedError

    @abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def refresh(self, obj: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def filter_query(self, model: Any, value_to_compare: Any, comparison_target) -> Any:
        raise NotImplementedError
