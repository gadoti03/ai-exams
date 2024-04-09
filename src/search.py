from io import BytesIO
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from src.exercise import Exercise

COLORS: Dict[str, str] = {
    'source': '#EC604A',
    'intermediate': '#37A2FC',
    'destination': '#71D937',
    'path': '#71D937',
    'explored': '#37A2FC'
}


class Search(Exercise):
    def __init__(self, source: str, destination: str, nodes: Dict[str, float], arcs: List[Tuple[str, str, float]]):
        """A search strategy exercise, defined by graph information."""

        # build graph
        graph = nx.DiGraph()
        for node, value in nodes.items():
            graph.add_node(node, value=value, color=COLORS['intermediate'])
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

        self.source: str = source
        self.destination: str = destination
        self.graph: nx.DiGraph = graph

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
        fig = plt.figure(figsize=(16, 16), tight_layout=True)
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
            label_pos=0.6,
            font_size=22,
            ax=fig.gca()
        )
        img = BytesIO()
        fig.savefig(img, bbox_inches='tight', pad_inches=0)
        doc.add_picture(img, width=Cm(10))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
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
        def draw_tree(tree: nx.DiGraph, path: List[int], heuristic: bool) -> plt.Figure:
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
            f = plt.figure(figsize=(16, 2.5 * levels), tight_layout=True)
            pos = nx.bfs_layout(tree, start=0, align='horizontal')
            pos = nx.rescale_layout_dict({node: (i, -j) for node, (i, j) in pos.items() if node in nodes}, scale=1)
            tree = tree.subgraph(nodes=nodes.keys())
            nx.draw(
                tree,
                pos=pos,
                node_size=10000,
                node_color=[COLORS['path' if node in path else 'explored'] for node in tree.nodes],
                linewidths=3,
                edgecolors='w',
                with_labels=True,
                labels={node: data['name'] for node, data in tree.nodes(data=True)},
                font_size=24,
                font_weight='bold',
                width=3,
                arrows=False,
                ax=f.gca()
            )
            nx.draw_networkx_labels(
                tree,
                pos={node: (i - 0.13, j + 0.02) for node, (i, j) in pos.items()},
                labels={node: data['step'] for node, data in nodes.items() if 'step' in data},
                bbox=dict(facecolor='white', edgecolor='red', boxstyle='square,pad=0.3'),
                font_size=20,
                ax=f.gca()
            )
            if heuristic:
                nx.draw_networkx_labels(
                    tree,
                    pos={node: (i, j + 0.15) for node, (i, j) in pos.items()},
                    labels={node: data['heuristic'] for node, data in nodes.items()},
                    bbox=dict(facecolor='white', edgecolor='white', boxstyle='round,pad=0.2'),
                    font_size=18,
                    ax=f.gca()
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

        def depth_first(tree: nx.DiGraph, step: int = 1, node: int = 0) -> bool:
            data = tree.nodes[node]
            data['step'] = step
            # base step (when destination is reached)
            if data['name'] == self.destination:
                return True
            solution = False
            # open all the successor nodes (to draw them) but explore recursively only if a solution is not found
            for child in self.graph.successors(data['name']):
                new = len(list(tree.nodes))
                tree.add_node(new, name=child, level=data['level'] + 1)
                tree.add_edge(node, new)
                if not solution:
                    solution = depth_first(node=new, step=step + 1, tree=tree)
            return solution

        def a_star(tree: nx.DiGraph, step: int = 1, node: int = 0) -> bool:
            data = tree.nodes[node]
            data['step'] = step
            # base step (when destination is reached)
            if data['name'] == self.destination:
                return True
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
            value = 1000
            for node, data in tree.nodes(data=True):
                if 'step' not in data and data['value'] <= value:
                    value = data['value']
                    best = node
            return a_star(node=best, step=step + 1, tree=tree)

        # depth first
        overestimated = check_heuristic()
        for text, fn, h in [('Depth-first search', depth_first, False), ('A*', a_star, True)]:
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
                assert fn(tree=t), f"No solution found by {text}"
                pth = get_path(t)
                fig = draw_tree(t, path=pth, heuristic=h)
                img = BytesIO()
                fig.savefig(img, bbox_inches='tight', pad_inches=0)
                doc.add_picture(img, width=Cm(12.5))
                doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                img.close()
                pth = [t.nodes[key]['name'] for key in pth]
                cst = sum([self.graph.edges[src, dst]['value'] for src, dst in zip(pth[:-1], pth[1:])])
                pth = ''.join(pth)
                doc.add_paragraph()
                doc.add_paragraph(f'The produced solution is {pth} with cost {cst}')
                if text != 'A*':
                    doc.add_paragraph()
