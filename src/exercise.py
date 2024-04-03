from abc import abstractmethod

from docx import Document


class Exercise:
    """Interface for an exercise in the exam."""

    @abstractmethod
    def text(self, doc: Document):
        pass

    @abstractmethod
    def solution(self, doc: Document):
        pass


class Dummy(Exercise):
    """Dummy exercise without any content."""

    def text(self, doc: Document):
        doc.add_paragraph('')

    def solution(self, doc: Document):
        doc.add_paragraph('')
