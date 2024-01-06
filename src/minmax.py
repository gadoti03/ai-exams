from typing import Tuple, Optional, Dict, Any

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.path import Path


class MinMaxTree:
    HEIGHT: int = 4
    """The height of the tree."""

    MIN: int = -1000
    """The minimum value in the alpha beta cuts."""

    MAX: int = 1000
    """The maximum value in the alpha beta cuts."""

    FIGSIZE: Tuple[int, int] = (21, 9)
    """The dimension of the output images."""

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
    def _draw_kwargs(leaves: bool) -> Dict[str, Any]:
        """A dictionary of nx.draw() arguments, depending on whether the drawn nodes are leaves or not."""
        kwargs = dict(
            arrows=False,
            edge_color='black',
            width=3,
            linewidths=3,
            font_family='arial'
        )
        if leaves:
            kwargs['node_shape'] = 's'
            kwargs['node_size'] = 2800
            kwargs['font_size'] = 21
            kwargs['font_weight'] = 'bold'
        else:
            w, h = 8, 2
            kwargs['node_shape'] = Path(np.array([[-w, -h], [-w, h], [w, h], [w, -h], [-w, -h]]))
            kwargs['node_size'] = 30000
            kwargs['font_size'] = 23
            kwargs['font_weight'] = 'normal'
        return kwargs

    @staticmethod
    def _draw(tree: nx.DiGraph, folder: Optional[str], name: str):
        """Draws the tree and stores the results in the given folder (or plots it if None) with its name."""
        # create data structures for leaf nodes, non-leaf nodes, and edges to be plotted separately
        leafs = {node: data for node, data in tree.nodes(data=True) if data['kind'] == 'leaf'}
        nodes = {node: data for node, data in tree.nodes(data=True) if data['kind'] != 'leaf'}
        edges = tree.edges(data=True)
        fig = plt.figure(figsize=MinMaxTree.FIGSIZE)
        # use the same plotting routine for leaf nodes, non leaf nodes, and edges
        # this is due to the fact that node_shape and node_size accept a single value only
        # but we need to distinguish between leaf nodes (squared) and non-leaf nodes (rectangular)
        for nodelist, edgelist, leaves in [(leafs, {}, True), (nodes, {}, False), ({}, edges, False)]:
            nx.draw(
                tree,
                nodelist=list(nodelist),
                edgelist=list(edgelist),
                pos=nx.get_node_attributes(tree, name='pos'),
                labels={node: data['label'] for node, data in nodelist.items()},
                edgecolors=[data['edge'] for data in nodelist.values()],
                node_color=[data['color'] for data in nodelist.values()],
                **MinMaxTree._draw_kwargs(leaves=leaves)
            )
        # if a folder is not passed, plot the output, otherwise store it in the folder
        if folder is None:
            fig.show()
        else:
            fig.gca().set_xlim(0, 1)
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
                    # use the min function to stick to http://homepage.ufp.pt/jtorres/ensino/ia/alfabeta.html
                    # which assigns the value of the minmax tree instead of sticking to the alpha and beta
                    node['value'] = min(node['value'], value)
                    new_beta = min(node['beta'], node['value'])
                    if alpha >= new_beta:
                        return new_beta
                    # change the value of beta later to stick to http://homepage.ufp.pt/jtorres/ensino/ia/alfabeta.html
                    # which updates its value only if the search continues
                    node['beta'] = new_beta
                # return the value rather than beta to stick to http://homepage.ufp.pt/jtorres/ensino/ia/alfabeta.html
                # which assigns the value of the minmax tree instead of sticking to the alpha and beta
                return node['value']
            else:
                node['value'] = MinMaxTree.MIN
                for child in children:
                    value = expand(key=child, alpha=max(node['alpha'], alpha), beta=beta)
                    # use the max function to stick to http://homepage.ufp.pt/jtorres/ensino/ia/alfabeta.html
                    # which assigns the value of the minmax tree instead of sticking to the alpha and beta
                    node['value'] = max(node['value'], value)
                    new_alpha = max(node['alpha'], node['value'])
                    if new_alpha >= node['beta']:
                        return new_alpha
                    # change the value of alpha later to stick to http://homepage.ufp.pt/jtorres/ensino/ia/alfabeta.html
                    # which updates its value only if the search continues
                    node['alpha'] = new_alpha
                # return the value rather than alpha to stick to http://homepage.ufp.pt/jtorres/ensino/ia/alfabeta.html
                # which assigns the value of the minmax tree instead of sticking to the alpha and beta
                return node['value']

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
