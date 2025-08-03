from io import BytesIO
from string import ascii_uppercase
from typing import Dict, List, Tuple, Optional,TypedDict

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

import sys, os

from src.exercise import Exercise

COLORS: Dict[str, str] = {
    'source': '#EC604A',
    'intermediate': '#37A2FC',
    'destination': '#71D937',
    'path': '#71D937',
    'explored': '#37A2FC'
}

LETTERS: List[str] = list(ascii_uppercase)


def arc(distance: int) -> float:
    # nodes that are "more distant" from the destination should have more connections
    probability = 0.85 ** distance
    return np.random.random() >= probability

def weight(distance: int) -> int:
    # nodes that are "more distant" between each other should have higher weights
    rnd = np.random.random_integers(8)
    return int(rnd + 1.25 * distance)


def heuristic(distance: int) -> int:
    # sample from gaussian and clip to the interval [1, shortest path value] to be a valid heuristic
    rnd = np.random.normal(loc=4, scale=3)
    return int(np.clip(rnd, a_min=1, a_max=distance))

class ExpansionNode(TypedDict):
    name: str
    value: float  # o int, dipende dai tuoi dati

class Expansion(TypedDict):
    name: str
    nodes: List[ExpansionNode]

class Search(Exercise):
    def __init__(self,
                 nodes: int | List[str] | Dict[str, float] = 7,
                 arcs: None | List[Tuple[str, str, float]] = None,
                 ords: None | Dict[str, float] = None,
                 destination: None | str = None,
                 source: str = 'A',
                 tiebreaker: str = None,
                 graph_ratio: float = 1,
                 level_ratio: float = 7,
                 label_offset: float = 0.13,
                 heuristic_offset: float = 0.1):
        """A search strategy exercise, defined by graph information."""

        # handle nodes
        if isinstance(nodes, int):
            nodes = {n: None for n in LETTERS[:nodes]}
        elif isinstance(nodes, list):
            nodes = {n: None for n in nodes}
        
        if ords is not None:
            try:
                self.ords = {k: float(v) for k, v in ords.items()}
            except (ValueError, TypeError):
                raise ValueError("ords deve contenere solo valori numerici convertibili in float")
        else:
            self.ords = None

        # pick destination
        if destination is None:
            destination = str(np.random.choice([n for n in nodes if n != source]))
        # handle arcs (i.e., build a graph where each node has a path to the destination)
        #  1. sort nodes from destination to source, with random shuffling for internal nodes
        #  2. iterate over each node
        #      a) if there is no path connecting the node to the destination, add a direct arc
        #      b) for each of the following node, add a direct arc with probability p
        #      c) when adding an arc, choose a random positive integer weight up to a maximal value
        #  3. whenever a node is connected directly to the destination, or it is connected to another node who has
        #     been already marked connected, the node itself becomes connected as there is a valid path
        if arcs is None:
            arcs = []
            nodelist = [n for n in nodes if n != source and n != destination]
            np.random.shuffle(nodelist)
            nodelist = [destination, *nodelist, source]
            connected = {n: n == destination for n in nodelist}
            for i, d in enumerate(nodelist):
                if not connected[d]:
                    # distance of node <d> from the destination (0)
                    value = weight(distance=i)
                    arcs.append((d, destination, float(value)))
                    connected[d] = True
                for j, s in enumerate(nodelist[i + 1:]):
                    # distance of node <s> from the destination (0)
                    if arc(distance=i + j + 1):
                        # distance of node <s> from node <d>
                        value = weight(distance=j + 1)
                        arcs.append((s, d, float(value)))
                        connected[s] = True
        

        # build graph
        graph = nx.DiGraph()
        for node, value in nodes.items():
            graph.add_node(node, color=COLORS['intermediate'])
        for (sour, dest, value) in arcs:
            graph.add_edge(sour, dest, value=value)

        # check validity of source/destination and change their label
        try:
            graph.nodes[source]['color'] = COLORS['source']
        except KeyError:
            raise KeyError(f"Source node '{source}' is not in the list of nodes {list(nodes)}")
        try:
            graph.nodes[destination]['color'] = COLORS['destination']
        except KeyError:
            raise KeyError(f"Destination node '{destination}' is not in the list of nodes {list(nodes)}")

        # handle heuristics
        sp, _ = nx.single_source_dijkstra(graph.reverse(), source=destination, weight='value')
        for node, path in sp.items():
            value = nodes[node]
            if node == destination:
                value = 0
            elif value is None:
                # distance (in terms of path weight) between the node and the destination
                value = heuristic(distance=path)
            graph.nodes[node]['value'] = value

        self.tiebreaker: str = tiebreaker
        self.graph_ratio: float = graph_ratio
        self.level_ratio: float = level_ratio
        self.label_offset: float = label_offset
        self.heuristic_offset: float = heuristic_offset
        self.source: str = source
        self.destination: str = destination
        self.graph: nx.DiGraph = graph

    @property
    def name(self) -> str:
        return 'search'

    @property
    def yaml(self) -> Optional[str]:
        output = f"source: {self.source}\n"
        output += f"destination: {self.destination}\n"
        output += "nodes:\n"
        for n, data in self.graph.nodes(data=True):
            output += f"  {n}: {data['value']}\n"
        output += "arcs:\n"
        for s, d, data in self.graph.edges(data=True):
            output += f"  - [ {s}, {d}, {data['value']} ]\n"
        output += f"graph_ratio: {self.graph_ratio}\n"
        output += f"level_ratio: {self.level_ratio}\n"
        output += f"label_offset: {self.label_offset}\n"
        output += f"heuristic_offset: {self.heuristic_offset}\n"
        return output

    def text(self, doc: Document):
        # print text
        doc.add_paragraph(f'Consider the following graph, where {self.source} is the initial node and '
                          f'{self.destination} the goal node. The number on each arc is the cost of the operator for '
                          f'the move, while the number in the square next to each node is the heuristic evaluation of '
                          f'the node itself, namely, its estimated distance from the goal.')
        doc.add_paragraph()
        # draw graph (circular layout with 90° rotation and horizontal mirroring obtained by swapping the coordinates)
        g = self.graph.copy()
        pos = nx.rescale_layout_dict({node: (-j, i) for node, (i, j) in nx.circular_layout(g).items()}, scale=1)
        fig = plt.figure(figsize=(16, 16 / self.graph_ratio), tight_layout=True)
        nx.draw(
            g,
            pos=pos,
            node_size=10000,
            node_color=[data['color'] for _, data in g.nodes(data=True)],
            linewidths=3,
            edgecolors='w',
            with_labels=True,
            font_size=40,
            font_weight='bold',
            width=3,
            arrowsize=30,
            arrows=True,
            ax=fig.gca()
        )
        nx.draw(
            g,
            pos=nx.rescale_layout_dict(pos, scale=1.25),
            edgelist=[],
            labels={node: data['value'] for node, data in g.nodes(data=True)},
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=1'),
            font_size=28,
            ax=fig.gca()
        )
        nx.draw_networkx_edge_labels(
            g,
            pos=pos,
            edge_labels={(sour, dest): data['value'] for sour, dest, data in g.edges(data=True)},
            bbox=dict(facecolor='white', edgecolor='white', boxstyle='round,pad=0.5'),
            label_pos=0.65,
            font_size=22,
            ax=fig.gca()
        )

        img = BytesIO()
        fig.savefig(img, bbox_inches='tight', pad_inches=0)
        doc.add_picture(img, width=Cm(10))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        '''
        # GENERATE IMAGES FOR TASK 3
        # Save to disk with a unique name
        import time

        timestamp = int(time.time())
        filename = f'graph_{timestamp}.png'

        img.seek(0)
        with open(filename, 'wb') as f:
            f.write(img.getbuffer())
        '''

        img.close()

        # print questions
        doc.add_paragraph()
        doc.add_paragraph('a)  Apply the depth-first search (do not consider the costs of the nodes), and draw the '
                          'developed search tree indicating the expansion order; in the case of non-determinism, '
                          'choose the nodes to expand according to the alphabetical order. What is the produced '
                          'solution and its cost?')
        doc.add_paragraph()
        doc.add_paragraph('b)  Apply search A*, and draw the developed search tree indicating the expansion order and '
                          'the value of the function f(n) for each node n. In the case of non-determinism, choose the '
                          'nodes to expand according to the alphabetical order. Consider as heuristic h(n) the one '
                          'indicated in the square next to each node in the figure. What is the produced solution and '
                          'its cost?')

    def solution(self, doc: Document):
        def draw_tree(tree: nx.DiGraph, path: List[int], heuristically: bool) -> plt.Figure:
            # store list of initial nodes and compute the number of levels
            nodes = {node: data for node, data in tree.nodes(data=True)}
            levels = np.max([data['level'] for data in nodes.values()])
            # create a copy of the tree and add at least one child to each non-leaf node
            tree = tree.copy()
            for node, data in nodes.items():
                if data['level'] != levels and len(list(tree.successors(node))) == 0:
                    for _ in range(data['level'], levels):
                        new = len(list(tree.nodes))
                        tree.add_edge(node, new)
                        node = new
            # run bfs to dispose nodes, then draw excluding the dummies
            f, ax = plt.subplots(1, 1, figsize=(16, 16 * levels / self.level_ratio), tight_layout=True)
            ax.margins(y=0.03 * levels, tight=True)
            pos = nx.bfs_layout(tree, start=0, align='horizontal')
            pos = nx.rescale_layout_dict({node: (i, -j) for node, (i, j) in pos.items() if node in nodes}, scale=1)
            tree = tree.subgraph(nodes=nodes.keys())
            nx.draw(
                tree,
                pos=pos,
                node_size=8000,
                node_color=[COLORS['path' if node in path else 'explored'] for node in tree.nodes],
                linewidths=3,
                edgecolors='w',
                with_labels=True,
                labels={node: data['name'] for node, data in tree.nodes(data=True)},
                font_size=24,
                font_weight='bold',
                width=3,
                arrows=False,
                ax=ax
            )
            nx.draw_networkx_labels(
                tree,
                pos={node: (i - self.label_offset, j + 0.02) for node, (i, j) in pos.items()},
                labels={node: data['step'] for node, data in nodes.items() if 'step' in data},
                bbox=dict(facecolor='white', edgecolor='red', boxstyle='square,pad=0.3'),
                font_size=20,
                ax=ax
            )
            if heuristically:
                nx.draw_networkx_labels(
                    tree,
                    pos={node: (i, j + self.heuristic_offset) for node, (i, j) in pos.items()},
                    labels={node: data['heuristic'] for node, data in nodes.items()},
                    bbox=dict(facecolor='white', edgecolor='white', boxstyle='round,pad=0.2'),
                    font_size=18,
                    ax=ax
                )
            return f

        def get_path(tree: nx.DiGraph) -> List[int]:
            # find the node in the last step, which must be the destination
            node = None
            step = 0
            for key, data in tree.nodes(data=True):
                if 'step' in data and data['step'] > step:
                    step = data['step']
                    node = key
            name = tree.nodes[node]['name']
            assert name == self.destination, f"Last step must be destination {self.destination}, got {name}"
            # compute the path by going up from the ancestors
            path = [node]
            while len(list(tree.predecessors(node))) > 0:
                predecessors = list(tree.predecessors(node))
                assert len(predecessors) == 1, f"Tree nodes must have a single parent, got {len(predecessors)}"
                node = predecessors[0]
                path.insert(0, node)
            return path

        def check_heuristic() -> List[str]:
            output = []
            # compute the shortest paths from destination back to source (on the reversed graph)
            sp, _ = nx.single_source_dijkstra(self.graph.reverse(), source=self.destination, weight='value')
            # return the list of overestimated values, which make the heuristic not admissible
            for node, length in sp.items():
                value = self.graph.nodes[node]['value']
                if value > length:
                    output.append(f'{node} (Heuristic = {value}, Path = {float(length)})')
            return output

        # depth first
        overestimated = check_heuristic()
        for text, fn, h in [('Depth-first search', self.depth_first, False), ('A*', self.a_star, True)]:
            doc.add_paragraph(f'a) {text}')
            doc.add_paragraph()
            if h and len(overestimated) > 0:
                doc.add_paragraph(f'Heuristic is not admissible since it overestimates nodes:')
                for n in overestimated:
                    doc.add_paragraph(f'- {n}')
            else:
                t = nx.DiGraph()
                val = self.graph.nodes[self.source]['value']
                t.add_node(0, name=self.source, level=1, cost=0.0, value=val, heuristic=f'f=0.0+{val}={val}')
                result_bool, result_int = fn(tree=t, visited={n: False for n in self.graph.nodes})
                assert result_bool, f"No solution found by {text}"  # Usa il bool per verificare se la soluzione è stata trovata
                pth = get_path(t)
                fig = draw_tree(t, path=pth, heuristically=h)
                img = BytesIO()
                fig.savefig(img, bbox_inches='tight', pad_inches=0)
                doc.add_picture(img, width=Cm(13.5))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                img.close()
                pth = [t.nodes[key]['name'] for key in pth]
                cst = sum([self.graph.edges[src, dst]['value'] for src, dst in zip(pth[:-1], pth[1:])])
                pth = ''.join(pth)
                doc.add_paragraph()
                doc.add_paragraph(f'The produced solution is {pth} with cost {cst}')
                if text != 'A*':
                    doc.add_paragraph()

    def depth_first(self, tree: nx.DiGraph, visited: Dict[str, bool], step: int = 1, node: int = 0) -> tuple[bool, int]:
        data = tree.nodes[node]
        data['step'] = step
        visited[data['name']] = True
        # base step (when destination is reached)
        if data['name'] == self.destination:
            return True, step
        solution = False
        # open all the successor nodes (to draw them) but explore recursively only if a solution is not found
        for child in self.graph.successors(data['name']):
            if visited[child]:
                continue
            new = len(list(tree.nodes))
            tree.add_node(new, name=child, level=data['level'] + 1)
            tree.add_edge(node, new)
            if not solution:
                solution = self.depth_first(node=new, visited=visited, step=step + 1, tree=tree)
        return solution

    def a_star(self, tree: nx.DiGraph, visited: Dict[str, bool], step: int = 1, node: int = 0) -> tuple[bool, int]:
        data = tree.nodes[node]
        data['step'] = step
        # base step (when destination is reached)
        if data['name'] == self.destination:
            return True, step
        # open all the successor nodes and compute their cost
        for child in self.graph.successors(data['name']):
            new = len(list(tree.nodes))
            value = self.graph.nodes[child]['value']
            cost = data['cost'] + self.graph.edges[(data['name'], child)]['value']
            tree.add_node(
                new,
                name=child,
                level=data['level'] + 1,
                cost=cost,
                value=cost + value,
                heuristic=f'f={cost}+{value}={cost + value}'
            )
            tree.add_edge(node, new)
        # select and open the unexplored node with the least function value
        best = None
        value = None
        name = None

        for node, data in tree.nodes(data=True):
            if 'step' not in data:
                if value is None or data['value'] < value:
                    value = data['value']
                    best = node
                    name = data['name']
                if data['value'] == value:
                    # alphabetical order
                    if self.tiebreaker=='alphabetical order' and data['name'] < name:
                        value = data['value']
                        best = node
                        name = data['name']
                    # order of nodes
                    if self.tiebreaker=='order of nodes' and self.ords[data['name']] < self.ords[name]:
                        value = data['value']
                        best = node
                        name = data['name']
        return self.a_star(node=best, visited=visited, step=step + 1, tree=tree)