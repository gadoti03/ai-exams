import numpy as np

from src.csp import CSP
from src.minmax import MinMaxTree
from src.questions import Questions

# results
folder = '../temp'

# minmax
tree = MinMaxTree(values=np.random.randint(low=-99, high=100, size=16))
show = True

# csp
problem = CSP()
domain = range(1, 5)
a = problem.variable(*domain, name='A')
b = problem.variable(*domain, name='B')
c = problem.variable(*domain, name='C')
d = problem.variable(*domain, name='D')
problem.constraint(a > b)
problem.constraint(c <= b + 1)
problem.constraint(c > d)
problem.constraint(a == d + 2)
assign = None
kind = 'fc'

# questions
faikr = 'move'
intsys = True

if __name__ == '__main__':
    # solve minmax and print/plot results if needed
    tree.exercise(folder=folder)
    tree.minmax(folder=folder)
    tree.alphabeta(folder=folder)
    if show:
        print('VALUES: [' + ', '.join([str(v) for v in tree.values]) + ']\n')
        tree.alphabeta()
    # handle the csp type
    if kind == 'arc':
        problem.consistency(folder=folder)
    elif kind == 'fc':
        problem.forward(folder=folder)
    elif kind == 'fla':
        problem.lookahead(assign=assign, folder=folder)
    else:
        raise AssertionError(f"Unknown csp kind '{kind}'")
    # handle questions
    if faikr is not None:
        Questions.faikr(action=faikr, folder=folder)
    if intsys:
        Questions.intsys(folder=folder)
