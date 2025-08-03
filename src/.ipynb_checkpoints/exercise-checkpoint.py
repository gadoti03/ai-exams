from abc import abstractmethod
from typing import Dict, Any, Optional

from docx import Document


class Exercise:
    """Interface for an exercise in the exam."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def yaml(self) -> Optional[str]:
        pass

    @abstractmethod
    def text(self, doc: Document):
        pass

    @abstractmethod
    def solution(self, doc: Document):
        pass


class Dummy(Exercise):
    """Dummy exercise without any content."""

    def __init__(self, name: str):
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def yaml(self) -> Optional[str]:
        return None

    def text(self, doc: Document):
        doc.add_paragraph('')

    def solution(self, doc: Document):
        doc.add_paragraph('')
