from typing import Optional

from docx import Document

from src.exercise import Exercise


class Planning(Exercise):
    def __init__(self, action: Optional[str]):
        self.action: str = action

    def text(self, doc: Document):
        raise NotImplementedError()

    def solution(self, doc: Document):
        raise NotImplementedError()

    def kowalski(self) -> str:
        raise NotImplementedError()

    def graphplan(self) -> str:
        raise NotImplementedError()
