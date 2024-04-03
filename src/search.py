from typing import Dict, List, Tuple

from docx import Document

from src.exercise import Exercise


class Search(Exercise):
    def __init__(self, source: str, destination: str, nodes: Dict[str, float], arcs: List[Tuple[str, str, float]]):
        pass

    def text(self, doc: Document):
        doc.add_paragraph()

    def solution(self, doc: Document):
        doc.add_paragraph()
