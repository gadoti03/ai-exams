from src.csp import CSP
from src.minmax import MinMaxTree

# results
folder = '../temp'

# minmax
values = None  # np.random.randint(low=-99, high=100, size=16)

# csp
consistency = True
problem = CSP()
a = problem.variable(0, 1, 2, 3, 4, 5, 6, 7, name='A')
b = problem.variable(0, 1, 2, 3, 4, 5, 6, 7, name='B')
c = problem.variable(0, 1, 2, 3, 4, 5, 6, 7, name='C')
problem.constraint(a + 1 <= b)
problem.constraint(a + 4 >= c)
problem.constraint(b + 3 <= c)

if __name__ == '__main__':
    if values is not None:
        print('VALUES: [' + ', '.join([str(v) for v in values]) + ']\n')
        tree = MinMaxTree(values=values)
        # store the results
        tree.exercise(folder=folder)
        tree.minmax(folder=folder)
        tree.alphabeta(folder=folder)
        # manually check the cuts
        tree.alphabeta()
    if consistency is True:
        problem.consistency(folder=folder)
    elif consistency is False:
        raise NotImplementedError()
