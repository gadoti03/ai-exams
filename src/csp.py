from abc import abstractmethod
from dataclasses import dataclass, field
from string import ascii_lowercase
from typing import Any, Callable, Literal, List, Optional, Tuple, Iterable

import numpy as np

LETTERS: List[str] = list(ascii_lowercase)
"""List of lowercase letters to index constraints."""

ORDINAL: List[str] = ['FIRST', 'SECOND', 'THIRD', 'FOURTH', 'FIFTH', 'SIXTH', 'SEVENTH', 'EIGHTH', 'NINTH', 'TENTH']
"""List of ordinal numbers to index iterations."""

VOWELS: List[str] = ['a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U']
"""List of vowels to match the article before the variable name."""

TAB: str = '  '
"""Tab spacing."""


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
            operation=lambda domain: domain + other,
            reverse=lambda domain: domain - other,
            name=f'{self.name} + {other}',
            csp=self.csp
        )

    def __radd__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda domain: domain + other,
            reverse=lambda domain: domain - other,
            name=f'{other} + {self.name}',
            csp=self.csp
        )

    def __sub__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda domain: domain - other,
            reverse=lambda domain: domain + other,
            name=f'{self.name} - {other}',
            csp=self.csp
        )

    def __rsub__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda domain: domain - other,
            reverse=lambda domain: domain + other,
            name=f'{other} - {self.name}',
            csp=self.csp
        )

    def __mul__(self, other: int):
        return Operation(
            parent=self,
            operation=lambda domain: domain * other,
            reverse=lambda domain: domain // other,
            name=f'{self.name} * {other}',
            csp=self.csp
        )

    def __rmul__(self, other):
        return Operation(
            parent=self,
            operation=lambda domain: domain * other,
            reverse=lambda domain: domain // other,
            name=f'{other} * {self.name}',
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

    operation: Callable[[np.ndarray], np.ndarray] = field()
    """The operation which is applied to the variable."""

    reverse: Callable[[np.ndarray], np.ndarray] = field()
    """The reverse of the variable's operation."""

    @property
    def domain(self) -> np.ndarray:
        # compute the domain from the parent's one
        return self.operation(self.parent.domain)

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
        assert isinstance(self._var2, Variable), f"Expected variable as var1, got {type(self._var2)}"

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
        """Reduces the domain of the involved variables (arc-consistency) and returns a tuple of booleans indicating
        whether the domain of the first and second variable have been changed, respectively."""
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


class CSP:
    """A CSP exercise instance."""

    def __init__(self):
        self._output: Optional[str] = None
        """The output of the CSP exercise."""

        self._variables: List[Domain] = []
        """The variables involved in the CSP."""

        self._constraints: List[Constraint] = []
        """The constraints involved in the CSP."""

    def variable(self, *domain: int, name: str) -> Variable:
        """Adds a variable in the CSP."""
        var = Domain(_domain=list(domain), name=name, csp=self)
        self._variables.append(var)
        return var

    def constraint(self, constraint: Callable[[Any], Constraint]) -> Constraint:
        """Adds a constraint in the CSP."""
        cst = constraint(self)
        assert cst.var1.csp == self, f"First variable {cst.var1} does not belong to this csp."
        assert cst.var2.csp == self, f"Second variable {cst.var2} does not belong to this csp."
        self._constraints.append(cst)
        return cst

    def consistency(self, folder: Optional[str] = None):
        """Performs arc-consistency on the CSP and stores the results in the given folder (or prints if None)."""
        assert self._output is None, "This csp has been already solved"
        self._output = ''
        finished = False
        iteration = 0
        # iterate until the domains are not changed
        while not finished:
            finished = True
            # log the initial iteration message
            message = '' if iteration == 0 else ' (since the domains have changed during the last one)'
            self._log(f'\n{ORDINAL[iteration]} ITERATION{message}:')
            # iterate over all the constraints
            for i, cst in enumerate(self._constraints):
                # log the constraint and apply the domain reduction
                self._log(f'\nApply ({ascii_lowercase[i]}) - {cst.name}')
                res1, res2 = cst.reduce()
                infeasible = False
                # for both the variables involved (and their result), log the results
                for var1, var2, res in [(cst.var1, cst.var2, res1), (cst.var2, cst.var1, res2)]:
                    article = 'an' if var2.name[0] in VOWELS else 'a'
                    self._log(f'{TAB}- For each {var1}, is there {article} {var2}?', end=' ')
                    # if the variable domain is null, the problem is infeasible (break the inner loop)
                    if len(var1.domain) == 0:
                        self._log(f'There is no assignment for {var1} which could satisfy the constraint.')
                        self._log('The problem is infeasible.')
                        infeasible = True
                        break
                    # if res = True, the domains did not change
                    elif res:
                        self._log(f'Yes.')
                    # otherwise, log the new domain.
                    else:
                        self._log(f'No. The only values of {var1} which admit a solution are {var1.string()}.')
                # if at least one domain was empty the problem is infeasible, hence break the outer loop
                if infeasible:
                    break
                # if both domains did not change, log a message
                elif res1 and res2:
                    self._log('Domains not changed.')
                # otherwise, log the new domains
                else:
                    self._log(f'New domains:')
                    for var in self._variables:
                        self._log(f'{var}::{var.string()}')
                        finished = False
            # increase iteration
            iteration += 1
        # log end
        self._log('\nALGORITHM TERMINATION.')
        # prepend the introduction of the solution, then log it with prepend = True
        introduction = 'By applying arc-consistency, the variables domains are reduced as follows:\n\n'
        for var in self._variables:
            introduction += f'{var}::{var.string()}\n'
        introduction += '\nAPPLIED REASONING:\n'
        introduction += '\nWe start with the following domains:\n'
        for var in self._variables:
            introduction += f'{var}::{var.string(original=True)}\n'
        introduction += '\nAnd with the following set of constraints:\n'
        for i, cst in enumerate(self._constraints):
            introduction += f'{ascii_lowercase[i]}) {cst}\n'
        self._log(introduction, end='', pre=True)
        # store the results
        self._save(folder=folder, name='consistency')

    def _log(self, message: str, end: str = '\n', pre: bool = False):
        """Logs a message in the output string (prepends if pre = True)."""
        if pre:
            self._output = message + end + self._output
        else:
            self._output = self._output + message + end

    def _save(self, folder: Optional[str], name: str):
        """Stores the output in the given folder (or prints it if None)."""
        if folder is None:
            print(self._output)
        else:
            with open(file=f'{folder}/{name}.txt', mode='w') as f:
                f.write(self._output)
