import itertools
from dataclasses import dataclass, field
from io import BytesIO
from typing import Dict, List, Literal, Tuple, Any, Set, Optional

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from src.exercise import Exercise

ActionType = Dict[Literal['params', 'precond', 'add', 'delete'], Any]

NOOP: str = 'no_op'


def join(values: list, sep: str = ', ') -> str:
    return '-' if len(values) == 0 else sep.join([str(v) for v in values])


@dataclass(frozen=True, repr=False, unsafe_hash=False)
class Proposition:
    """A proposition in the planning exercise."""

    name: str = field()
    params: Tuple[str, ...] = field()

    @property
    def key(self) -> str:
        """A unique key representing the action."""
        return self.name if len(self.params) == 0 else f'{self.name}({join(self.params)})'

    def ground(self, mapping: Dict[str, str]) -> 'Proposition':
        """Grounds some terms in the parameters via a mapping function and returns a new proposition."""
        return Proposition(name=self.name, params=tuple([mapping.get(p, p) for p in self.params]))

    def __repr__(self) -> str:
        return self.key

    def __eq__(self, other: Any):
        return str(self) == str(other)


@dataclass(frozen=True, repr=False, unsafe_hash=False)
class Action:
    """An action in the planning exercise."""

    # none represents no-op operation
    name: str = field()
    variables: Dict[str, Set[str]] = field(default_factory=dict)
    precond: Tuple[Proposition, ...] = field(default=tuple())
    delete: Tuple[Proposition, ...] = field(default=tuple())
    add: Tuple[Proposition, ...] = field(default=tuple())

    def __post_init__(self):
        for delete in self.delete:
            assert delete in self.precond, f"Deleted action '{delete}' is not in precondition of action '{self}'"

    @property
    def key(self) -> str:
        """A unique key representing the action."""
        return self.name if len(self.variables) == 0 else f'{self.name}({join(self.variables)})'

    @property
    def assignments(self) -> List[Dict[str, str]]:
        """Returns the cartesian product of all possible variable assignments."""
        output = []
        keys, choices = [], []
        for k, c in self.variables.items():
            keys.append(k)
            choices.append(c)
        for assignment in itertools.product(*choices):
            # ignore assignments with duplicate values as an all-different constraint is implied from common sense
            if len(np.unique(assignment)) == len(assignment):
                output.append({k: v for k, v in zip(keys, assignment)})
        return output

    def instantiate(self, **assignment: Dict[str, str]) -> 'Action':
        assert len(assignment) == len(self.variables), f"Expected {len(self.variables)} values, got {len(assignment)}"
        if len(assignment) == 0:
            return self
        for var, val in assignment.items():
            choices = self.variables[var]
            assert val in choices, f"Expected value in {choices} for variable '{var}', got '{val}'"
        return Action(
            name=f'{self.name}({join(assignment.values())})',
            variables=dict(),
            precond=[pr.ground(assignment) for pr in self.precond],
            delete=[pr.ground(assignment) for pr in self.delete],
            add=[pr.ground(assignment) for pr in self.add]
        )

    def __str__(self) -> str:
        return self.key

    def __repr__(self):
        return f'{self}\nPRECOND: {join(self.precond)}\nDELETE: {join(self.delete)}\nADD: {join(self.add)}'


class Planning(Exercise):
    def __init__(self,
                 init: List[List[str]],
                 goal: List[List[str]],
                 graph_ratio: float = 3,
                 **actions: Dict[str, ActionType]):
        """A planning exercise defined by initial state, goal, and a set of actions."""

        act = {}
        for name, action in actions.items():
            var = action['variables']
            act[name] = Action(
                name=name,
                variables={} if var is None else {k: set(v) for k, v in var.items()},
                precond=tuple([Proposition(name=pr[0], params=tuple(pr[1:])) for pr in action['precond']]),
                delete=tuple([Proposition(name=pr[0], params=tuple(pr[1:])) for pr in action['delete']]),
                add=tuple([Proposition(name=pr[0], params=tuple(pr[1:])) for pr in action['add']])
            )

        self.init: Set[Proposition] = [Proposition(name=pr[0], params=tuple(pr[1:])) for pr in init]
        """The initial state of the planning problem."""

        self.goal: Set[Proposition] = [Proposition(name=pr[0], params=tuple(pr[1:])) for pr in goal]
        """The goal state of the planning problem."""

        self.actions: Dict[str, Action] = act
        """The actions involved in the planning problem."""

        self.graph_ratio: float = graph_ratio
        """The width of the graphplan solution image."""

    @property
    def name(self) -> str:
        return 'planning'

    @property
    def yaml(self) -> Optional[str]:
        output = "init:\n"
        for proposition in self.init:
            output += f"  - [ " + ", ".join([proposition.name] + [param for param in proposition.params]) + " ]\n"
        output += "\ngoal:\n"
        for proposition in self.goal:
            output += f"  - [ " + ", ".join([proposition.name] + [param for param in proposition.params]) + " ]\n"
        for name, action in self.actions.items():
            output += f"\n{name}:\n"
            output += "  variables:\n"
            for variable, values in action.variables.items():
                output += f"    {variable}: [ {', '.join(values)} ]\n"
            output += "  precond:\n"
            for proposition in action.precond:
                output += f"    - [ " + ", ".join([proposition.name] + [param for param in proposition.params]) + " ]\n"
            output += "  delete:\n"
            for proposition in action.delete:
                output += f"    - [ " + ", ".join([proposition.name] + [param for param in proposition.params]) + " ]\n"
            output += "  add:\n"
            for proposition in action.add:
                output += f"    - [ " + ", ".join([proposition.name] + [param for param in proposition.params]) + " ]\n"
        output += f"\ngraph_ratio: {self.graph_ratio}\n"
        return output

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
        # create execution graph with nodes indexed by name and level, then add no-op actions for initial propositions
        graph = nx.DiGraph()
        no_ops = [Action(name=f'no_op on {str(pr)}', variables={}, precond=(pr,), add=(pr,)) for pr in self.init]
        # iterate through all the available actions to ground them for level 1
        for action in [*no_ops, *self.actions.values()]:
            # create a list of possible assignments from cartesian products between
            for assignment in action.assignments:
                # assign values to the variables
                instance = action.instantiate(**assignment)
                # if all the preconditions are satisfied, we can insert this action in level 1
                # additionally, we link it to its preconditions and to its add/delete effects
                if np.all([precond in self.init for precond in instance.precond]):
                    graph.add_node((instance.key, 1), value=instance)
                    for precond in instance.precond:
                        graph.add_node((precond.key, 0), value=precond)
                        graph.add_edge((precond.key, 0), (instance.key, 1), delete=False)
                    for add in instance.add:
                        graph.add_node((add.key, 2), value=add)
                        graph.add_edge((instance.key, 1), (add.key, 2), delete=False)
                    for delete in instance.delete:
                        graph.add_node((delete.key, 2), value=delete)
                        graph.add_edge((instance.key, 1), (delete.key, 2), delete=True)
        # print the graph (first, merge all no_op nodes into a single node)
        g = graph.copy()
        g.add_node((NOOP, 1), value=None)
        for pr in self.init:
            nx.contracted_nodes(g, (NOOP, 1), (f'no_op on {pr}', 1), copy=False)
        for node in g.nodes():
            g.nodes[node]['label'] = node[0]
            g.nodes[node]['level'] = node[1]
        pos = nx.multipartite_layout(g, subset_key='level')
        fig = plt.figure(figsize=(21, 21 / self.graph_ratio), tight_layout=True)
        nx.draw_networkx_nodes(g, pos=pos, ax=fig.gca())
        nx.draw_networkx_labels(
            g,
            pos=pos,
            labels={node: data['label'] for node, data in g.nodes(data=True)},
            font_size=24,
            bbox=dict(facecolor='white', edgecolor='white', boxstyle='square,pad=1'),
            ax=fig.gca(),
        )
        for delete, style in [(False, 'solid'), (True, (0, [5, 5]))]:
            nx.draw_networkx_edges(
                g,
                pos=pos,
                edgelist=[(sour, dest) for sour, dest, data in g.edges(data=True) if data['delete'] is delete],
                width=3,
                style=style,
                ax=fig.gca()
            )
        fig.gca().spines['top'].set_visible(False)
        fig.gca().spines['right'].set_visible(False)
        fig.gca().spines['bottom'].set_visible(False)
        fig.gca().spines['left'].set_visible(False)
        img = BytesIO()
        fig.savefig(img, bbox_inches='tight', pad_inches=0)
        doc.add_picture(img, width=Cm(18.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        img.close()
        # print inconsistent actions and propositions (first, build data of all possible values)
        actions, propositions, consistent = [], [], set()
        for (_, level), data in graph.nodes(data=True):
            if level == 1:
                actions.append(data['value'])
            elif level == 2:
                propositions.append(data['value'])
        # loop over each pair of possible actions
        for i, a1 in enumerate(actions):
            for a2 in actions[i + 1:]:
                a1_required = {*a1.precond, *a1.add}
                a2_required = {*a2.precond, *a2.add}
                a1_incompatible = np.any([delete in a2_required for delete in a1.delete])
                a2_incompatible = np.any([delete in a1_required for delete in a2.delete])
                # if an action deletes a proposition in the preconditions/add list of the other, print incompatibility
                if a1_incompatible or a2_incompatible:
                    p = doc.add_paragraph()
                    for act, end in [(a1, ' and '), (a2, ' are incompatible')]:
                        if NOOP in act.name:
                            p.add_run(NOOP).bold = True
                            p.add_run(' on ')
                            p.add_run(act.key.split(' on ')[1]).bold = True
                        else:
                            p.add_run(act.key).bold = True
                        p.add_run(end)
                # otherwise store all pair of generated propositions in the 'consistent' set
                # since there is a consistent path to generate them
                else:
                    added = [*a1.add, *a2.add]
                    consistent.update({(p1, p2) for i, p1 in enumerate(added) for p2 in added[i + 1:]})
        doc.add_paragraph()
        # loop over each pari of possible propositions
        for i, p1 in enumerate(propositions):
            for p2 in propositions[i + 1:]:
                # if the pair is not in the consistent set, there is no path to reach them
                if (p1, p2) not in consistent and (p2, p1) not in consistent:
                    p = doc.add_paragraph()
                    p.add_run(p1.key).bold = True
                    p.add_run(' and ')
                    p.add_run(p2.key).bold = True
                    p.add_run(' are incompatible')
