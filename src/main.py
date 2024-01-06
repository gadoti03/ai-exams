import numpy as np

from src.minmax import MinMaxTree

# results
folder = '../temp'

# minmax
values = np.random.randint(low=-99, high=100, size=16)

# csp
# TODO

if __name__ == '__main__':
    if values is not None:
        print('VALUES: [' + ', '.join([str(v) for v in values]) + ']\n')
        tree = MinMaxTree(values=values)
        # store the results
        tree.exercise(folder=folder)
        tree.minmax(folder=folder)
        tree.alphabeta(folder=folder)
        # manually check the cuts
        tree.alphabeta(folder=None)
