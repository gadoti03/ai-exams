from abc import abstractmethod
from dataclasses import dataclass, field
from string import ascii_lowercase
from typing import Any, Callable, Literal, List, Optional, Tuple, Iterable, Dict

import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm
from sympy.parsing.sympy_parser import parse_expr

from src.exercise import Exercise

LETTERS: List[str] = list(ascii_lowercase)
"""List of lowercase letters to index constraints."""

ORDINAL: List[str] = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth']
"""List of ordinal numbers to index iterations."""

VOWELS: List[str] = ['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']
"""List of vowels to match the article before the variable name."""

TAB: int = 12
"""Tab spacing."""

LONG_TAB: int = 16
"""Long tab spacing."""


@dataclass(frozen=False, eq=False, repr=False)
class Variable:
    """A Variable in the CSP."""

    name: str = field()
    """The name of the variable."""

    csp: Any = field()
    """The CSP containing the variable."""

    @property
    @abstractmethod
    def domain(self) -> np.ndarray:
        """The domain of the variable."""
        pass

    @domain.setter
    @abstractmethod
    def domain(self, domain: Iterable[int]):
        pass

    def equal(self, domain: List[int]) -> bool:
        """Checks whether the given domain is equal to the variable domain."""
        if len(self.domain) != len(domain):
            return False
        domain = np.array(domain)
        return np.all(self.domain == domain)

    def __repr__(self) -> str:
        return self.name

    # VARIABLE OPERATIONS

    def __add__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda: self.domain + other,
            reverse=lambda codomain: codomain - other,
            name=f'{self.name} + {other}',
            csp=self.csp
        )

    def __radd__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda: self.domain + other,
            reverse=lambda codomain: codomain - other,
            name=f'{other} + {self.name}',
            csp=self.csp
        )

    def __sub__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda: self.domain - other,
            reverse=lambda codomain: codomain + other,
            name=f'{self.name} - {other}',
            csp=self.csp
        )

    def __rsub__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda: other - self.domain,
            reverse=lambda codomain: other - codomain,
            name=f'{other} - {self.name}',
            csp=self.csp
        )

    def __mul__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda: self.domain * other,
            reverse=lambda codomain: codomain // other,
            name=f'{self.name} * {other}',
            csp=self.csp
        )

    def __rmul__(self, other):
        return Operation(
            parent=self,
            operation=lambda: self.domain * other,
            reverse=lambda codomain: codomain // other,
            name=f'{other} * {self.name}',
            csp=self.csp
        )

    def __mod__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda: np.array(list({v % other for v in self.domain})),
            reverse=lambda codomain: np.array([v for v in self.domain if v % other in codomain]),
            name=f'{self.name} % {other}',
            csp=self.csp
        )

    # VARIABLE COMPARISONS

    def __eq__(self, other) -> Callable:
        return lambda csp: Constraint(_var1=self, _var2=other, operator='=', csp=csp)

    def __lt__(self, other) -> Callable:
        return lambda csp: Constraint(_var1=self, _var2=other, operator='<', csp=csp)

    def __le__(self, other) -> Callable:
        return lambda csp: Constraint(_var1=self, _var2=other, operator='<=', csp=csp)

    def __gt__(self, other) -> Callable:
        return lambda csp: Constraint(_var1=self, _var2=other, operator='>', csp=csp)

    def __ge__(self, other) -> Callable:
        return lambda csp: Constraint(_var1=self, _var2=other, operator='>=', csp=csp)


@dataclass(frozen=False, eq=False, repr=False)
class Domain(Variable):
    """A user-defined variable, which has its own specific domain."""

    _domain: List[int] = field()
    """The domain of the variable, which may change during the solution process."""

    _original_domain: List[int] = field(init=False, default_factory=list)
    """The original domain of the variable."""

    def __post_init__(self):
        self._original_domain.extend(self._domain)

    @property
    def domain(self) -> np.ndarray:
        return np.array(self._domain)

    @domain.setter
    def domain(self, domain: Iterable[int]) -> None:
        self._domain.clear()
        self._domain.extend(list(domain))

    @property
    @abstractmethod
    def original_domain(self) -> np.ndarray:
        """The original domain of the variable."""
        return np.array(self._original_domain)

    def string(self, original: bool = False) -> str:
        """Return a string representation of the variable's domain (or original domain, if original = True)."""
        domain = self._original_domain if original else self._domain
        # if the domain is a range with more than two values, use the compact representation [lb..ub]
        if len(domain) > 2 and domain == list(range(domain[0], domain[-1] + 1)):
            return f'[{domain[0]}..{domain[-1]}]'
        else:
            return '[' + ', '.join([str(i) for i in domain]) + ']'


@dataclass(frozen=False, eq=False, repr=False)
class Operation(Variable):
    """A Variable which is the result of a unary operation on another variable."""

    parent: Variable = field()
    """The parent of the variable."""

    operation: Callable[[], np.ndarray] = field()
    """The operation which is applied to the variable."""

    reverse: Callable[[np.ndarray], np.ndarray] = field()
    """The reverse of the variable's operation."""

    @property
    def domain(self) -> np.ndarray:
        # compute the domain from the parent's one
        return self.operation()

    @domain.setter
    def domain(self, domain: Iterable[int]):
        # compute the reverse domain and assign it to the parent
        domain = self.reverse(np.array(domain))
        self.parent.domain = domain


@dataclass(frozen=True, repr=False)
class Constraint:
    """A Binary Constraint in the CSP."""

    # BASIC CONSTRAINTS OPERATIONS

    @staticmethod
    def _equal(value: int, domain: np.ndarray) -> bool:
        return value in domain

    @staticmethod
    def _lower_than(value: int, domain: np.ndarray) -> bool:
        return value < domain.max()

    @staticmethod
    def _lower_equal(value: int, domain: np.ndarray) -> bool:
        return value <= domain.max()

    @staticmethod
    def _greater_than(value: int, domain: np.ndarray) -> bool:
        return value > domain.min()

    @staticmethod
    def _greater_equal(value: int, domain: np.ndarray) -> bool:
        return value >= domain.min()

    OPERATORS = {
        '=': ('equal', 'equal'),
        '<': ('lower_than', 'greater_than'),
        '<=': ('lower_equal', 'greater_equal'),
        '>': ('greater_than', 'lower_than'),
        '>=': ('greater_equal', 'lower_equal')
    }
    """Operations attached to the operator aliases."""

    _var1: Variable = field()
    """The first variable involved in the binary constraint."""

    _var2: Variable = field()
    """The second variable involved in the binary constraint."""

    operator: Literal['=', '<', '<=', '>', '>='] = field()
    """The constraint operator."""

    csp: Any = field()
    """The CSP containing the constraint."""

    def __post_init__(self):
        assert isinstance(self._var1, Variable), f"Expected variable as var1, got {type(self._var1)}"
        assert isinstance(self._var2, Variable), f"Expected variable as var2, got {type(self._var2)}"

    def __repr__(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return f"{self._var1} {self.operator} {self._var2}"

    @property
    def var1(self) -> Domain:
        """The original first variable involved in the constraint."""
        # climb the list of parents until a Domain is found
        var = self._var1
        while isinstance(var, Operation):
            var = var.parent
        return var

    @property
    def var2(self) -> Domain:
        """The original second variable involved in the constraint."""
        # climb the list of parents until a Domain is found
        var = self._var2
        while isinstance(var, Operation):
            var = var.parent
        return var

    def reduce(self) -> Tuple[bool, bool]:
        """Reduces the domain of the involved variables and returns a tuple of booleans indicating whether the domain
        of the first and second variable have been changed, respectively."""
        var1, var2 = self._var1, self._var2
        dom1, dom2 = var1.domain, var2.domain
        check1, check2 = self.OPERATORS[self.operator]
        result = {}
        for var, domain, check in [(var1, dom2, check1), (var2, dom1, check2)]:
            check = getattr(Constraint, f'_{check}')
            new_domain = [v for v in var.domain if check(v, domain)]
            result[var.name] = var.equal(domain=new_domain)
            var.domain = new_domain
        return result[var1.name], result[var2.name]


class CSP(Exercise):

    def __init__(self,
                 variables: Dict[str, List[int]],
                 constraints: List[str],
                 kind: Optional[Literal['consistency', 'forward', 'lookahead']] = None,
                 assign: Optional[int] = None):
        """A CSP exercise instance defined by its variables and constraints. The 'kind' parameter defines which type of
        exercise to build, either Arc Consistency, Forward Checking, or Full Lookahead (if 'kind' is None, a random
        type will be selected). The 'assign' parameter is used in Full Lookahead only and defines the value to be
        assigned to the first variable (if None, a random value will be selected).
        """
        self._variables: List[Domain] = [Domain(_domain=dom, name=var, csp=self) for var, dom in variables.items()]
        """The variables involved in the CSP."""

        self._constraints: List[Constraint] = []
        """The constraints involved in the CSP."""

        local = {v.name: v for v in self._variables}
        for cst in constraints:
            exp = parse_expr(cst, local_dict=local, evaluate=True)
            try:
                self._constraints.append(exp(self))
            except AssertionError:
                raise AssertionError(f"Error with constraint: {cst} "
                                     f"(either the constraint is not binary or it involves undefined variables)")

        kind = np.random.choice(['consistency', 'forward', 'lookahead']) if kind is None else kind
        if kind == 'lookahead':
            assign = np.random.choice(self._variables[0].domain) if assign is None else assign
        else:
            assign = None

        self.kind: Literal['consistency', 'forward', 'lookahead'] = kind
        """The kind of exercise to build."""

        self.assign: Optional[int] = assign
        """The assignment of the first variable in Full Lookahead (or None if a different kind is selected)."""

    def text(self, doc: Document):
        doc.add_paragraph('Given the following CSP:')
        doc.add_paragraph()
        for var in self._variables:
            doc.add_paragraph(f'{var}::{var.string(original=True)}')
        doc.add_paragraph()
        for cst in self._constraints:
            doc.add_paragraph(f'{cst}')
        doc.add_paragraph()
        if self.kind == 'consistency':
            doc.add_paragraph('Apply Arc Consistency to the CSP and show the final domains of the variables.')
        elif self.kind == 'forward':
            p = doc.add_paragraph('Find the first solution through tree search, by applying Forward Checking, ')
            p.add_run('using alphabetical order of variables and lexicographic order of values.')
        elif self.kind == 'lookahead':
            p = doc.add_paragraph('Apply Full Lookahead to the CSP, and show the domains of the variables when ')
            p.add_run(f'{self._variables[0]}').bold = True
            p.add_run(' is instantiated to ')
            p.add_run(f'{self.assign}').bold = True
            p.add_run(' (consider the variables according to the numerical order).')
        else:
            raise AssertionError(f"Unknown exercise kind '{self.kind}'")

    def solution(self, doc: Document):
        if self.kind == 'consistency':
            self._consistency(doc)
        elif self.kind == 'forward':
            self._forward(doc)
        elif self.kind == 'lookahead':
            self._lookahead(doc)
        else:
            raise AssertionError(f"Unknown exercise kind '{self.kind}'")

    def _consistency(self, doc: Document):
        """Performs arc-consistency on the CSP and prints the results."""
        # start the solution computation by iterating until the domains are not changed
        iteration = 0
        finished = False
        p0 = doc.add_paragraph()  # keep reference to first paragraph to prepend the final solution
        infeasible = False
        while not finished:
            finished = True
            # log the initial iteration message
            p = doc.add_paragraph()
            p.add_run(f'{ORDINAL[iteration]} Iteration').italic = True
            if iteration != 0:
                p.add_run(' (since the domains have changed during the last one)').italic = True
            p.add_run(':').italic = True
            doc.add_paragraph()
            # iterate over all the constraints
            for i, cst in enumerate(self._constraints):
                # log the constraint and apply the domain reduction
                p = doc.add_paragraph(f'Apply ({ascii_lowercase[i]}) - ')
                p.add_run(cst.name).bold = True
                res1, res2 = cst.reduce()
                # for both the variables involved (and their result), log the results
                for v1, v2, res in [(cst.var1, cst.var2, res1), (cst.var2, cst.var1, res2)]:
                    article = 'an' if v2.name[0] in VOWELS else 'a'
                    p = doc.add_paragraph(f'  - For each {v1}, is there {article} {v2}? ')
                    # if the variable domain is null, the problem is infeasible (break the inner loop)
                    if len(v1.domain) == 0:
                        p.add_run(f'There is no assignment for {v1} which could satisfy the constraint.')
                        doc.add_paragraph('The problem is infeasible.')
                        infeasible = True
                        break
                    # if res = True, the domains did not change
                    elif res:
                        p.add_run('Yes.')
                    # otherwise, log the new domain.
                    else:
                        p.add_run(f'No. The only values of {v1} which admit a solution are {v1.string()}.')
                # if at least one domain was empty the problem is infeasible, hence break the outer loop
                if infeasible:
                    doc.add_paragraph()
                    finished = True
                    break
                # if both domains did not change, log a message
                elif res1 and res2:
                    doc.add_paragraph('Domains not changed.')
                    doc.add_paragraph()
                # otherwise, log the new domains
                else:
                    finished = False
                    doc.add_paragraph(f'New domains:')
                    for var in self._variables:
                        doc.add_paragraph(f'{var}::{var.string()}')
                    doc.add_paragraph()
            # increase iteration
            iteration += 1
        # log end
        p = doc.add_paragraph()
        p.add_run('Algorithm Termination.').italic = True
        # prepend the introduction of the solution
        if infeasible:
            p0.insert_paragraph_before('By applying arc-consistency, we find that the problem is infeasible:')
            p0.insert_paragraph_before()
            p = p0.insert_paragraph_before()
            r = p.add_run('Applied Reasoning')
            r.bold = True
            r.italic = True
        else:
            p0.insert_paragraph_before('By applying arc-consistency, the variables domains are reduced as follows:')
            for var in self._variables:
                p0.insert_paragraph_before(f'{var}::{var.string()}')
            p0.insert_paragraph_before()
            p = p0.insert_paragraph_before()
            r = p.add_run('Applied Reasoning')
            r.bold = True
            r.italic = True
            p0.insert_paragraph_before()
            p0.insert_paragraph_before('We start with the following domains:')
            for var in self._variables:
                p0.insert_paragraph_before(f'{var}::{var.string(original=True)}')
            p0.insert_paragraph_before()
            p0.insert_paragraph_before('And with the following set of constraints:')
            for cst in self._constraints:
                p0.insert_paragraph_before(f'{cst}')

    def _forward(self, doc: Document):
        """Performs forward check on the CSP and prints the result."""
        rows = []

        # recursively try to find solution by checking variables' domains iteratively
        def solve(idx: int, domains: List[np.ndarray]) -> bool:
            # if we arrive to the point where there are no more variables left, then the problem is solver
            if idx == len(self._variables):
                return True
            # otherwise, retrive the variable and iterate over its current domain
            variable = self._variables[idx]
            for value in domains[idx]:
                # assign the current value as new domain and iterate through the constraints
                fail = False
                variable.domain = [value]
                for cst in self._constraints:
                    # when the variable appears in the constraint, perform the reduction and check for feasibility
                    if cst.var1.name == variable.name or cst.var2.name == variable.name:
                        cst.reduce()
                        if len(cst.var1.domain) == 0 or len(cst.var2.domain) == 0:
                            fail = True
                            break
                # log the results based on whether the process failed or not
                row = ['Backtracking' if fail else 'Labeling & FC']
                post_fail = False
                # for each variable, log:
                #   - var = domains[i][0] (a unique value since already assigned) for previous variables
                #   - var = value if the variable is the one being assigned
                #   - FAIL if the variable failed
                #   - domain if the variable did not fail
                #   - '///' if the variable comes after one who failed
                for i, var in enumerate(self._variables):
                    if i < idx:
                        row.append(f'{var} = {domains[i][0]}')
                    elif i == idx:
                        row.append(f'{var} = {value}')
                    elif post_fail:
                        row.append(f'---')
                    elif len(var.domain) == 0:
                        row.append(f'Fail')
                        post_fail = True
                    else:
                        row.append(var.string())
                rows.append(row)
                # in case of the procedure did not fail and the problem can be solved, return true
                if not fail and solve(idx=idx + 1, domains=[var.domain.copy() for var in self._variables]):
                    return True
                # otherwise, restore the initial domains
                for i, var in enumerate(self._variables):
                    var.domain = domains[i]
            return False

        # start to solve from the first variable
        solved = solve(idx=0, domains=[v.domain.copy() for v in self._variables])
        # log the initial information
        for v in self._variables:
            doc.add_paragraph(f'{v}::{v.string(original=True)}')
        doc.add_paragraph()
        for c in self._constraints:
            doc.add_paragraph(f'{c}')
        doc.add_paragraph()
        table = doc.add_table(1, len(self._variables) + 1)
        table.rows[0].height = Cm(0.65)
        cells = table.rows[0].cells
        for n, v in enumerate(self._variables):
            cells[n + 1].text = v.name
            cells[n + 1].paragraphs[0].runs[0].font.bold = True
        for cells in rows:
            r = table.add_row()
            r.height = Cm(0.65)
            for n, c in enumerate(cells):
                r.cells[n].text = c
                if c == 'Fail':
                    r.cells[n].paragraphs[0].runs[0].font.bold = True
                    r.cells[n].paragraphs[0].runs[0].font.italic = True
        # log only if infeasible
        if not solved:
            doc.add_paragraph()
            doc.add_paragraph('The problem is infeasible.')
        table.alignment = WD_ALIGN_PARAGRAPH.CENTER
        table.style = 'Table Grid'

    def _lookahead(self, doc: Document):
        """Performs full look-ahead on the CSP and prints the results."""
        # assigns the value to the new domain
        var = self._variables[0]
        assert self.assign in var.domain, f"Domain of {var} is {var.domain}, trying to assign value {self.assign}"
        self._variables[0].domain = [self.assign]
        # print the initial text
        doc.add_paragraph('We start from the CSP:')
        doc.add_paragraph()
        for v in self._variables:
            doc.add_paragraph(f'{v}::{var.string(original=True)}')
        doc.add_paragraph()
        for c in self._constraints:
            doc.add_paragraph(f'{c}')
        doc.add_paragraph()
        p = doc.add_paragraph()
        r = p.add_run('Apply Full Lookahead starting from the constraints involving variable ')
        r.bold = True
        r.italic = True
        p.add_run(f'{var}').bold = True
        r = p.add_run(':')
        r.bold = True
        r.italic = True
        doc.add_paragraph()
        # order the constraints depending on whether the assigned variable appears or not
        constraints = {'var': [], 'other': []}
        for cst in self._constraints.copy():
            key = 'var' if (cst.var1.name == var.name or cst.var2.name == var.name) else 'other'
            constraints[key].append(cst)
        # iterate over the constraints while keeping track of feasibility
        feasible = True
        for cst in [cst for key, cst_list in constraints.items() for cst in cst_list]:
            # apply the constraints
            cst.reduce()
            doc.add_paragraph(f'Apply {cst}:')
            if len(cst.var1.domain) == 0 or len(cst.var2.domain) == 0:
                doc.add_paragraph(f' There is no assignment which could satisfy the constraint.')
                feasible = False
                break
            else:
                doc.add_paragraph(f' {cst.var1}::{cst.var1.string()}')
                doc.add_paragraph(f' {cst.var2}::{cst.var2.string()}')
            doc.add_paragraph()
        # if the problem is feasible, log the final domains
        p = doc.add_paragraph()
        if feasible:
            p.add_run('The final domains are:').italic = True
            doc.add_paragraph(f' {var} = {self.assign}')
            for var in self._variables[1:]:
                doc.add_paragraph(f' {var}::{var.string()}')
        else:
            p = doc.add_paragraph()
            p.add_run('The problem is infeasible.').italic = True
