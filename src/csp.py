from abc import abstractmethod
from dataclasses import dataclass, field
from string import ascii_lowercase
from typing import Any, Callable, Literal, List, Optional, Tuple, Iterable, Dict

import numpy as np

LETTERS: List[str] = list(ascii_lowercase)
"""List of lowercase letters to index constraints."""

ORDINAL: List[str] = ['FIRST', 'SECOND', 'THIRD', 'FOURTH', 'FIFTH', 'SIXTH', 'SEVENTH', 'EIGHTH', 'NINTH', 'TENTH']
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


class CSP:
    """A CSP exercise instance."""

    def __init__(self):
        self._output: Optional[Dict[str, str]] = None
        """The output of the CSP exercise (text and solution)."""

        self._variables: List[Domain] = []
        """The variables involved in the CSP."""

        self._constraints: List[Constraint] = []
        """The constraints involved in the CSP."""

    def variable(self, *domain: int, name: str) -> Variable:
        """Adds a variable in the CSP."""
        assert name not in [v.name for v in self._variables], f"There is already a variable named '{name}' in the csp"
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
        # initialize the exercise with the correct text
        self._init('Apply the Arc-consistency to the CSP and show the final domains of the variables.')
        # start the solution computation by iterating until the domains are not changed
        iteration = 0
        finished = False
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
                    self._log(f'  - For each {var1}, is there {article} {var2}?', end=' ')
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
        self._save(folder=folder, name='arc')

    def forward(self, folder: Optional[str] = None):
        """Performs forward check on the CSP and stores the results in the given folder (or prints if None)."""
        # initialize the exercise with the correct text
        exercise = 'Find the first solution through tree search, by applying forward checking, '
        exercise += 'using alphabetical order of variables and lexicographic order of values.'
        self._init(exercise)

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
                self._log('Backtracking ' if fail else 'Labeling & FC', end=' ' * (LONG_TAB - 13) + ' | ')
                post_fail = False
                # for each variable, log:
                #   - var = domains[i][0] (a unique value since already assigned) for previous variables
                #   - var = value if the variable is the one being assigned
                #   - FAIL if the variable failed
                #   - domain if the variable did not fail
                #   - '///' if the variable comes after one who failed
                for i, var in enumerate(self._variables):
                    if i < idx:
                        msg = f'{var} = {domains[i][0]}'
                    elif i == idx:
                        msg = f'{var} = {value}'
                    elif post_fail:
                        msg = f'///'
                    elif len(var.domain) == 0:
                        msg = f'FAIL'
                        post_fail = True
                    else:
                        msg = var.string()
                    self._log(msg, end=' ' * (TAB - len(msg)) + ' | ')
                self._log()
                # in case of the procedure did not fail and the problem can be solved, return true
                if not fail and solve(idx=idx + 1, domains=[var.domain.copy() for var in self._variables]):
                    return True
                # otherwise, restore the initial domains
                for i, var in enumerate(self._variables):
                    var.domain = domains[i]
            return False

        # log the initial information
        for v in self._variables:
            self._log(f'{v}::{v.string(original=True)}')
        self._log()
        for c in self._constraints:
            self._log(str(c))
        self._log('\n', end=' ' * LONG_TAB + ' | ')
        for v in self._variables:
            self._log(v.name, end=' ' * (TAB - len(v.name)) + ' | ')
        self._log('\n' + '-' * (LONG_TAB + 3 + (TAB + 3) * len(self._variables)))
        # start to solve from the first variable and log only if infeasible
        if not solve(idx=0, domains=[v.domain.copy() for v in self._variables]):
            self._log('\nThe problem is infeasible.')
        # store the results
        self._save(folder=folder, name='fc')

    def lookahead(self, assign: int, folder: Optional[str] = None):
        """Performs full look-ahead on the CSP and stores the results in the given folder (or prints if None).
        The assign value is assigned to the first variable in the CSP."""
        # assigns the value to the new domain
        var = self._variables[0]
        assert assign in var.domain, f"Domain of variable {var} is {var.domain}, trying to assign value {assign}"
        self._variables[0].domain = [assign]
        # initialize the exercise with the correct text
        exercise = f'Apply the Full Look Ahead (FLA) to the CSP, and show the domains of the variables when {var} is '
        exercise += f'instantiated to {assign} (consider the variables according to the numerical order).'
        self._init(exercise=exercise)
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
            self._log(f'Apply {cst}:')
            if len(cst.var1.domain) == 0 or len(cst.var2.domain) == 0:
                self._log(f'There is no assignment which could satisfy the constraint.')
                self._log('The problem is infeasible.')
                feasible = False
                break
            else:
                self._log(f'{cst.var1}::{cst.var1.string()}')
                self._log(f'{cst.var2}::{cst.var2.string()}')
            self._log()
        # if the problem is feasible, log the final domains
        if feasible:
            self._log('\nFinal Domains:')
            self._log(f'{var} = {assign}')
            for var in self._variables[1:]:
                self._log(f'{var}::{var.string()}')
        # store the results
        self._save(folder=folder, name='fla')

    def _init(self, exercise: str):
        """Initializes the solution process."""
        # check that the problem was not already solved
        assert self._output is None, "This csp has been already solved"
        # build the exercise text
        text = 'Given the following CSP:\n\n'
        for var in self._variables:
            text += f'{var}::{var.string(original=True)}\n'
        text += '\n'
        for cst in self._constraints:
            text += f'{cst}\n'
        text += f'\n{exercise}'
        # initialize the output
        self._output = dict(text=text, solution='')

    def _log(self, message: str = '', end: str = '\n', pre: bool = False, solution: bool = True):
        """Logs a message in the output string (prepends if pre = True), either the text or the solution."""
        key = 'solution' if solution else 'text'
        if pre:
            self._output[key] = message + end + self._output[key]
        else:
            self._output[key] = self._output[key] + message + end

    def _save(self, folder: Optional[str], name: str):
        """Stores the output in the given folder (or prints it if None)."""
        if folder is None:
            for key, output in self._output.items():
                print(f'{key.upper()}:')
                print(output)
                print()
        else:
            for key, output in self._output.items():
                with open(file=f'{folder}/{name}_{key}.txt', mode='w') as f:
                    f.write(output)
