from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import SourceBundle


class PatentSource(ABC):
    name: str

    @abstractmethod
    def load_bundle(self) -> SourceBundle:
        raise NotImplementedError

