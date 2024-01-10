import numpy as np

from src.csp import CSP
from src.game import Game
from src.questions import Questions
from src.training import Training

# results
folder = 'temp'

# game
game = Game(values=np.random.randint(low=-99, high=100, size=16))
show = True

# training
training = Training(
    output='Test',
    framework={'V1', 'V2'},
    plane={'Airbus', 'Boeing', 'Comac'}
)

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
kind = 'consistency'

# questions
faikr = 'move'
intsys = True

if __name__ == '__main__':
    # solve minmax and print/plot results if needed
    game.exercise(folder=folder)
    game.minmax(folder=folder)
    game.alphabeta(folder=folder)
    if show:
        print('VALUES: [' + ', '.join([str(v) for v in game.values]) + ']\n')
        game.alphabeta()
    # solve the training set exercise
    training.solve(folder=folder)
    # handle the csp type
    if kind == 'consistency':
        problem.consistency(folder=folder)
    elif kind == 'forward':
        problem.forward(folder=folder)
    elif kind == 'lookahead':
        problem.lookahead(assign=assign, folder=folder)
    else:
        raise AssertionError(f"Unknown csp kind '{kind}'")
    # handle questions
    if faikr is not None:
        Questions.faikr(action=faikr, folder=folder)
    if intsys:
        Questions.intsys(folder=folder)
