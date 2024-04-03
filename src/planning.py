from dataclasses import dataclass, field
from typing import Dict, List, Literal, Tuple

from docx import Document

from src.exercise import Exercise

Action = Dict[Literal['params', 'precond', 'add', 'delete'], list]


def join(values: list, sep: str = ', ') -> str:
    return '-' if len(values) == 0 else sep.join([str(v) for v in values])


@dataclass(frozen=True)
class Proposition:
    """A proposition in the planning exercise."""

    name: str = field()
    params: Tuple[str, ...] = field()

    def __str__(self) -> str:
        return self.name if len(self.params) == 0 else f'{self.name}({join(self.params)})'


@dataclass(frozen=True)
class Action:
    """An action in the planning exercise."""

    name: str = field()
    variables: Tuple[str, ...] = field()
    precond: Tuple[Proposition, ...] = field()
    delete: Tuple[Proposition, ...] = field()
    add: Tuple[Proposition, ...] = field()

    def __str__(self) -> str:
        return self.name if len(self.variables) == 0 else f'{self.name}({join(self.variables)})'


class Planning(Exercise):
    def __init__(self, init: List[List[str]], goal: List[List[str]], **actions: Dict[str, Action]):
        """A planning exercise defined by initial state, goal, and a set of actions."""

        self.init: List[Proposition] = [Proposition(name=pr[0], params=tuple(pr[1:])) for pr in init]
        """The initial state of the planning problem."""

        self.goal: List[Proposition] = [Proposition(name=pr[0], params=tuple(pr[1:])) for pr in goal]
        """The goal state of the planning problem."""

        self.actions: Dict[str, Action] = {name: Action(
            name=name,
            variables=tuple(action['variables']),
            precond=tuple([Proposition(name=pr[0], params=tuple(pr[1:])) for pr in action['precond']]),
            delete=tuple([Proposition(name=pr[0], params=tuple(pr[1:])) for pr in action['delete']]),
            add=tuple([Proposition(name=pr[0], params=tuple(pr[1:])) for pr in action['add']]),
        ) for name, action in actions.items()}
        """The actions involved in the planning problem."""

    def text(self, doc: Document):
        doc.add_paragraph('Given the following initial state:')
        p = doc.add_paragraph()
        p.add_run(join(self.init)).bold = True
        doc.add_paragraph()
        doc.add_paragraph('Given the following actions:')
        for action in self.actions.values():
            p = doc.add_paragraph()
            p.add_run(f'{action}').bold = True
            doc.add_paragraph(f'PRECOND: {join(action.precond)}')
            doc.add_paragraph(f'DELETE: {join(action.delete)}')
            doc.add_paragraph(f'ADD: {join(action.add)}')
            doc.add_paragraph()
        doc.add_paragraph('We have to reach the goal:')
        p = doc.add_paragraph()
        p.add_run(join(self.goal)).bold = True

    def solution(self, doc: Document):
        p = doc.add_paragraph()
        p.add_run('<INSERT PLANNING SOLUTION>').bold = True

    def kowalski(self, doc: Document, action: str):
        """Prints the kowalski formulation."""
        act = self.actions.get(action)
        assert act is not None, f"Valid actions for planning are {list(self.actions)}, got '{action}'"
        p = doc.add_paragraph()
        p.add_run('Initial State').bold = True
        for pr in self.init:
            doc.add_paragraph(f'holds({pr}, s0)')
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run(f'Action: {act}').bold = True
        # add list
        for pr in act.add:
            doc.add_paragraph(f'hold({pr}, do({act}, S))')
        # precondition actions (pact)
        if len(act.precond) > 0:
            precond = join([f'holds({pr}, S)' for pr in act.precond], sep=' & ')
            doc.add_paragraph(f'pact({act}, S) :- {precond}')
        # delete list
        if len(act.delete) > 0:
            delete = join(act.delete, sep=' & ')
            doc.add_paragraph(f'holds(V, do({act}, S) :- holds(V, S), V \\= {delete}')

    def graphplan(self, doc: Document):
        """Prints the graphplan."""
        doc.add_paragraph()
