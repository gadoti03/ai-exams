from typing import Tuple, Optional, Dict, Any

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.path import Path


def rectangle(width: float, height: float) -> Path:
    """Builds a rectangle path."""
    vertices = np.array([[-width, -height], [-width, height], [width, height], [width, -height], [-width, -height]])
    return Path(vertices)


class MinMaxTree:
    HEIGHT: int = 4
    """The height of the tree."""

    MIN: int = -1000
    """The minimum value in the alpha beta cuts."""

    MAX: int = 1000
    """The maximum value in the alpha beta cuts."""

    FIGSIZE: Tuple[int, int] = (21, 9)
    """The dimension of the output images."""

    DRAW_KWARGS = dict(arrows=False, edge_color='black', width=2, linewidths=2)
    """A dictionary of nx.draw() arguments."""

    NODE_STYLE: Dict[str, Any] = dict(
        default=(rectangle(width=7, height=2), 20000),
        leaf=('s', 2000)
    )
    """Defines the shape and size of the node based on its kind."""

    BORDER_COLOR: Dict[str, str] = dict(
        leaf='#000000',
        max='#EB220C',
        min='#00A2FF'
    )
    """Defines the color of the node border based on its kind."""

    NODE_COLOR: Dict[str, str] = dict(
        best='#FFFF00',
        cut='#FFFFFF',
        exercise='#FFFFFF',
        default='#D6D5D5'
    )
    """Defines the color of the node based on its kind."""

    @staticmethod
    def _draw(tree: nx.DiGraph, folder: Optional[str], name: str):
        """Draws the tree and stores the results in the given folder (or plots it if None) with its name."""
        # create data structures for leaf nodes, non-leaf nodes, and edges to be plotted separately
        leafs = {n: d for n, d in tree.nodes(data=True) if d['kind'] == 'leaf'}
        nodes = {n: d for n, d in tree.nodes(data=True) if d['kind'] != 'leaf'}
        edges = tree.edges()
        fig = plt.figure(figsize=MinMaxTree.FIGSIZE)
        # use the same plotting routine for leaf nodes, non leaf nodes, and edges
        # this is due to the fact that node_shape and node_size accept a single value only
        # but we need to distinguish between leaf nodes (squared) and non-leaf nodes (rectangular)
        for nodelist, edgelist, kind in [(leafs, [], 'leaf'), (nodes, [], 'default'), ({}, edges, 'default')]:
            shape, size = MinMaxTree.NODE_STYLE[kind]
            nx.draw(
                tree,
                nodelist=list(nodelist),
                edgelist=list(edgelist),
                pos=nx.get_node_attributes(tree, name='pos'),
                labels=nx.get_node_attributes(tree, name='label'),
                edgecolors=[d['edge'] for d in nodelist.values()],
                node_color=[d['color'] for d in nodelist.values()],
                node_shape=shape,
                node_size=size,
                **MinMaxTree.DRAW_KWARGS
            )
        # if a folder is not passed, plot the output, otherwise store it in the folder
        if folder is None:
            fig.show()
        else:
            fig.savefig(f'{folder}/{name}.png')

    def __init__(self, values: np.ndarray):
        """Creates the minmax tree using a nx.DiGraph structure where the leaf nodes have the given values."""
        assert len(values) == 2 ** MinMaxTree.HEIGHT, f"Expected {2 ** MinMaxTree.HEIGHT} values, got {len(values)}"
        self.tree = nx.balanced_tree(r=2, h=MinMaxTree.HEIGHT, create_using=nx.DiGraph)
        for height in range(MinMaxTree.HEIGHT + 1):
            for element in range(2 ** height):
                previous = 2 ** height
                key = previous + element - 1
                node = self.tree.nodes[key]
                node['key'] = key
                node['layer'] = height
                node['element'] = element
                node['pos'] = (2 * element + 1) / (2 * previous), -height
                if height == MinMaxTree.HEIGHT:
                    node['kind'] = 'leaf'
                    node['edge'] = MinMaxTree.BORDER_COLOR['leaf']
                    node['value'] = values[element]
                    node['parent'] = key // 2
                else:
                    node['kind'] = 'max' if height % 2 == 0 else 'min'
                    node['edge'] = MinMaxTree.BORDER_COLOR[node['kind']]
                    node['value'] = None
                    node['left'] = 2 * key + 1
                    node['right'] = 2 * key + 2
                    if height != 0:
                        node['parent'] = key // 2

    def exercise(self, folder: Optional[str] = None):
        """Draws the exercise image and stores the results in the given folder (or plots it if None)."""
        tree = self.tree.copy()
        # for each node, set the appropriate color and assign a blank label for non-leaf ones
        for node, data in tree.nodes(data=True):
            node = tree.nodes[node]
            if data['kind'] == 'leaf':
                node['color'] = MinMaxTree.NODE_COLOR['default']
                node['label'] = node['value']
            else:
                node['color'] = MinMaxTree.NODE_COLOR['exercise']
                node['label'] = ''
        MinMaxTree._draw(tree, folder=folder, name='exercise')

    def minmax(self, folder: Optional[str] = None):
        """Draws the minmax solution and stores the results in the given folder (or plots it if None)."""
        tree = self.tree.copy()

        def expand(key: int) -> float:
            # retrieve the node and assign the default color
            node = tree.nodes[key]
            node['color'] = MinMaxTree.NODE_COLOR['default']
            # when a leaf is found, simply return its value
            if node['kind'] == 'leaf':
                node['label'] = node['value']
                return node['value']
            # otherwise, expand the children and assign the value as min/max depending on the node type
            children = [node['left'], node['right']]
            values = [expand(key=c) for c in children]
            best = np.argmax(values) if node['kind'] == 'max' else np.argmin(values)
            # if we are in the root node, color its best children
            if node['layer'] == 0:
                best_choice = tree.nodes[children[best]]
                best_choice['color'] = MinMaxTree.NODE_COLOR['best']
            node['label'] = values[best]
            return values[best]

        # start the expansion from the root
        expand(key=0)
        MinMaxTree._draw(tree, folder=folder, name='minmax')

    def alphabeta(self, folder: Optional[str] = None):
        """Draws the alphabeta solution and stores the results in the given folder (or plots it if None)."""
        tree = self.tree.copy()

        def expand(key: int, alpha: int, beta: int, cut: bool) -> float:
            node = tree.nodes[key]
            # when a node is cut, assign a blank label and expand its successors with cut = True
            if cut:
                node['label'] = ''
                node['color'] = MinMaxTree.NODE_COLOR['cut']
                if node['kind'] == 'leaf':
                    return node['value']
                else:
                    children = node['left'], node['right']
                    function = np.min if node['kind'] == 'min' else np.max
                    return function([expand(key=child, alpha=alpha, beta=beta, cut=True) for child in children])
            # otherwise, assign the default color and when a leaf is found, simply return its value
            node['color'] = MinMaxTree.NODE_COLOR['cut'] if cut else MinMaxTree.NODE_COLOR['default']
            if node['kind'] == 'leaf':
                node['label'] = node['value']
                return node['value']
            # otherwise, first assign alpha and beta, then retrieve the children
            node['alpha'] = alpha
            node['beta'] = beta
            node['label'] = None
            children = [node['left'], node['right']]
            # distinguish strategy based on whether this is a min or max node
            if node['kind'] == 'min':
                node['value'] = MinMaxTree.MAX
                for child in children:
                    # if the node is not cut, proceed with the alpha beta, otherwise simply expand
                    if not cut:
                        value = expand(key=child, alpha=alpha, beta=min(node['beta'], beta), cut=False)
                        node['value'] = min(node['value'], value)
                        beta = min(node['beta'], node['value'])
                        if alpha >= beta:
                            cut = True
                            # this is needed to stick to http://homepage.ufp.pt/jtorres/ensino/ia/alfabeta.html
                            # which does not update the latest beta value if alpha >= beta
                            node['label'] = f"{node['alpha']}/{node['value']}/{node['beta']}"
                        node['beta'] = beta
                    else:
                        expand(key=child, alpha=alpha, beta=beta, cut=True)
                if node['label'] is None:
                    node['label'] = f"{node['alpha']}/{node['value']}/{node['beta']}"
                return node['beta']
            else:
                node['value'] = MinMaxTree.MIN
                for child in children:
                    # if the node is not cut, proceed with the alpha beta, otherwise simply expand
                    if not cut:
                        value = expand(key=child, alpha=max(node['alpha'], alpha), beta=beta, cut=cut)
                        node['value'] = max(node['value'], value)
                        alpha = max(node['alpha'], node['value'])
                        if alpha >= beta:
                            cut = True
                            # this is needed to stick to http://homepage.ufp.pt/jtorres/ensino/ia/alfabeta.html
                            # which does not update the latest beta value if alpha >= beta
                            node['label'] = node['label'] = f"{node['alpha']}/{node['value']}/{node['beta']}"
                        node['alpha'] = alpha
                    else:
                        expand(key=child, alpha=max(node['alpha'], alpha), beta=beta, cut=cut)
                # if we are in the root node (max only), color its best children
                if node['layer'] == 0:
                    for child in children:
                        child = tree.nodes[child]
                        child['color'] = MinMaxTree.NODE_COLOR['best' if child['value'] == node['value'] else 'default']
                if node['label'] is None:
                    node['label'] = f"{node['alpha']}/{node['value']}/{node['beta']}"
                return node['alpha']

        expand(key=0, alpha=MinMaxTree.MIN, beta=MinMaxTree.MAX, cut=False)
        MinMaxTree._draw(tree, folder=folder, name='alphabeta')

    def alphabeta_alternative(self, folder: Optional[str] = None):
        """Draws the alphabeta solution and stores the results in the given folder (or plots it if None).
        (Alternative version where labels and colors are post-processed rather than computed recursively)"""
        tree = self.tree.copy()

        def expand(key: int, alpha: int, beta: int) -> float:
            # retrieve the node and assign the default color plus a visited flag
            node = tree.nodes[key]
            node['visited'] = True
            node['color'] = MinMaxTree.NODE_COLOR['default']
            # when a leaf is found, simply return its value
            if node['kind'] == 'leaf':
                node['label'] = node['value']
                return node['value']
            # otherwise, first assign alpha and beta, then retrieve the children
            node['alpha'] = alpha
            node['beta'] = beta
            children = [node['left'], node['right']]
            # distinguish strategy based on whether this is a min or max node
            if node['kind'] == 'min':
                node['value'] = MinMaxTree.MAX
                for child in children:
                    value = expand(key=child, alpha=alpha, beta=min(node['beta'], beta))
                    node['value'] = min(node['value'], value)
                    new_beta = min(node['beta'], node['value'])
                    if alpha >= new_beta:
                        return new_beta
                    node['beta'] = new_beta
                return node['beta']
            else:
                node['value'] = MinMaxTree.MIN
                for child in children:
                    value = expand(key=child, alpha=max(node['alpha'], alpha), beta=beta)
                    node['value'] = max(node['value'], value)
                    new_alpha = max(node['alpha'], node['value'])
                    if new_alpha >= node['beta']:
                        return new_alpha
                    node['alpha'] = new_alpha
                return node['alpha']

        expand(key=0, alpha=MinMaxTree.MIN, beta=MinMaxTree.MAX)
        # post-process the tree to assign the correct label and color
        for n, d in tree.nodes(data=True):
            n = tree.nodes[n]
            if 'visited' not in d:
                n['label'] = ''
                n['color'] = MinMaxTree.NODE_COLOR['cut']
            elif d['kind'] == 'leaf':
                n['label'] = n['value']
            else:
                n['label'] = f"{n['alpha']}/{n['value']}/{n['beta']}"
        # color the best children
        root, left, right = tree.nodes[0], tree.nodes[1], tree.nodes[2]
        left['color'] = MinMaxTree.NODE_COLOR['best' if left['value'] == root['value'] else 'default']
        right['color'] = MinMaxTree.NODE_COLOR['best' if right['value'] == root['value'] else 'default']
        MinMaxTree._draw(tree, folder=folder, name='alphabeta')
