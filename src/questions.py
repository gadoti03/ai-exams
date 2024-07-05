from typing import List, Optional

import numpy as np
from docx import Document

from src.exercise import Exercise
from src.planning import Planning


class Questions(Exercise):
    NUM: int = 3
    """The number of questions to select from the list of options."""

    FAIKR: List[str] = [
        'What are the main features of iterative deepening?',
        'What are the main features of a local search algorithm?',
        'What are the main features of a swarm intelligence algorithm?',
        'What are the main approaches of deductive planning. Explain the main differences.',
        'What are metaheuristics? Describe the main algorithms that have been presented during the course.',
        'What are non-informed search strategies? Describe the strategies that have been presented during the course.',
        'What is ant colony optimization?',
        'What is modal truth criterion and why it has been defined.',
        'What is conditional planning and which are its main features?',
        'What is Particle Swarm Optimization and which are its main features?',
        'What is hierarchical planning and explain the method presented during the course.',
        'What is Breadth-First Search? Describe this search strategy and discuss its completeness.',
        'What is arc-consistency? Describe the algorithm to achieve it. Explain the properties of values that are'
        ' removed from constraints and of values that are left in the domains.'
    ]
    """The list of options for faikr questions."""

    INTSYS: List[str] = [
        'How do top down ILP algorithms work?',
        'Which is the model of a neural network that enables competitive learning?',
        'What are the hierarchical planning approaches seen during the course?',
        'What are the main features of decision trees compared to neural networks?',
        'What is backpropagation?',
        'What is the theta-subsumption lattice?',
        'What is conditional planning and which are its main features?',
        'What is reinforcement learning and which tasks it solves best?',
        'What is the ant colony algorithm and which are its main features?',
        'What is the modal truth criterion and for what reason it has been defined.',
        'What is the difference between sensing and causal actions? Why and in which type of planners are they used?'
    ]
    """The list of options for intsys questions."""

    def __init__(self, planning: Optional[Planning], exam: str, kowalski: Optional[str] = None):
        """Selects the open questions for the final exercise, plus the additional exercises related to planning."""
        if planning is not None and kowalski is None and exam == 'faikr':
            kowalski = np.random.choice(list(planning.actions))

        self.planning: Optional[Planning] = planning
        self.kowalski: Optional[str] = kowalski
        self.exam: str = exam

    @property
    def name(self) -> str:
        return 'questions'

    @property
    def yaml(self) -> Optional[str]:
        output = f"exam: {self.exam}\n"
        output += f"kowalski: {'null' if self.kowalski is None else self.kowalski}\n"
        return output

    def text(self, doc: Document):
        if self.exam == 'faikr':
            p = doc.add_paragraph(' 1)  Model the action ')
            p.add_run(self.kowalski).bold = True
            p.add_run(' (preconditions, effects and frame axioms), and the ')
            p.add_run('initial state').bold = True
            p.add_run(' of the Exercise 4 using the Kowalsky formulation')
            doc.add_paragraph(' 2)  Build two levels of graph plan for the Exercise 4.')
            questions = Questions.FAIKR
            n = 3
        elif self.exam == 'intsys':
            doc.add_paragraph(' 1)  Build two levels of graph plan for the Exercise 3.')
            questions = Questions.INTSYS
            n = 2
        else:
            raise AssertionError(f"Unknown exam '{self.exam}'")
        for i, q in enumerate(np.random.choice(questions, size=Questions.NUM, replace=False)):
            doc.add_paragraph(f' {i + n})  {q}')

    def solution(self, doc: Document):
        if self.exam == 'faikr':
            doc.add_paragraph(f'1) Kowalski formulation of the initial state and action {self.kowalski}')
            doc.add_paragraph()
            if self.planning is not None:
                self.planning.kowalski(doc, action=self.kowalski)
                doc.add_paragraph()
            doc.add_paragraph('2) Graph Plan')
            if self.planning is not None:
                self.planning.graphplan(doc)
        elif self.exam == 'intsys':
            p = doc.add_paragraph()
            p.add_run(' Graphplan').bold = True
            if self.planning is not None:
                self.planning.graphplan(doc)
        else:
            raise AssertionError(f"Unknown exam '{self.exam}'")
