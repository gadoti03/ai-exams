import argparse
import heapq
import os
import shutil
import subprocess
import sys
import random
import yaml

from collections import defaultdict
from datetime import datetime

import networkx as nx
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.node import NodesList
from src.search import Search

current_folder = "scripts"

def check_consistency(edges_with_costs, heuristics):
    """
    Checks the consistency of the heuristic function for a list of edges with costs.
    
    edges_with_costs: a list of tuples (u, v, cost) representing the edges with their respective costs.
    h: a dictionary containing the heuristic values for each node {node: heuristic}.
    
    Returns True if the graph is consistent, False otherwise.
    """
    for u, v, cost in edges_with_costs:
        if heuristics[u] > cost + heuristics[v]:
            return False
    return True

def restore_backup(source_folder: str, backup_folder: str) -> None:
    """
    Restore a folder from its backup.

    Parameters:
    - source_folder (str): The original folder to restore.
    - backup_folder (str): The backup folder to use for restoration.
    """
    if os.path.exists(source_folder):
        shutil.rmtree(source_folder)
    os.rename(backup_folder, source_folder)


def build_yaml(exam: str, date: str, heuristics: dict, edges_with_costs: list) -> str:
    """
    Build the YAML content as a string.

    Args:
    - exam (str): Name of the exam.
    - date (str): Date in 'dd-mm-yyyy' or 'yyyy-mm-dd' format.
    - heuristics (dict): Dictionary of node heuristics {node: value}.
    - edges_with_costs (list): List of edges with costs [(u, v, cost), ...].

    Returns:
    - yaml_str (str): The constructed YAML as a string.
    """
    yaml_str = ""

    yaml_str += f"exam: {exam}\n"
    yaml_str += f"date: {date}\n"
    yaml_str += "exercises:\n"
    yaml_str += "  search:\n"
    yaml_str += "    source: A\n"
    yaml_str += "    destination: G\n"
    yaml_str += "    tiebreaker: alphabetical order\n"
    yaml_str += "    nodes:\n"

    for node in sorted(heuristics, key=lambda x: (x == 'G', x)):
        yaml_str += f"      {node}: {heuristics[node]}\n"

    yaml_str += "    arcs:\n"
    for u, v, cost in edges_with_costs:
        yaml_str += f"      - [{u}, {v}, {cost}]\n"

    yaml_str += "    graph_ratio: 1.0\n"
    yaml_str += "    level_ratio: 7.0\n"
    yaml_str += "    label_offset: 0.13\n"
    yaml_str += "    heuristic_offset: 0.1\n"

    return yaml_str

def dijkstra_from_goal(graph, goal):
    """
    Compute the shortest path distances from the goal node to all other nodes
    in a weighted directed graph using Dijkstra's algorithm.
    
    Args:
        graph (dict): A dictionary where each key is a node and the value is a list 
                      of (neighbor, weight) pairs.
        goal (str or int): The node from which to start the distances computation.
        
    Returns:
        dict: A dictionary mapping each node to its minimum distance from the goal node.
    """
    dist = {node: float('inf') for node in graph}
    dist[goal] = 0
    heap = [(0, goal)]
    
    while heap:
        current_dist, u = heapq.heappop(heap)
        if current_dist > dist[u]:
            continue
        for neighbor, weight in graph[u]:
            new_dist = current_dist + weight
            if new_dist < dist.get(neighbor, float('inf')):
                dist[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))
    return dist

def create_results_folder(path=".", base_name="results"):
    """
    Create a new folder to store results. 
    If a folder with the same name already exists, appends a counter to create a unique folder name.
    
    Args:
        path (str): The parent directory where the folder will be created.
        base_name (str): The desired name for the results folder.
        
    Returns:
        str: The absolute path to the newly created folder.
    """
    path = os.path.abspath(path)
    
    folder_name = os.path.join(path, base_name)
    counter = 1
    while os.path.exists(folder_name):
        folder_name = os.path.join(path, f"{base_name}({counter})")
        counter += 1
    os.makedirs(folder_name)
    return folder_name

def copy_contents(src, dst):
    """
    Copy all files and subdirectories from the source directory to the destination directory.
    If a subdirectory already exists in the destination, merge the contents.

    Args:
        src (str): Path to the source directory.
        dst (str): Path to the destination directory.
    """
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dst_path)

def get_exponential_intervals(n, base=2):
    """
    Returns n exponentially decreasing probability intervals normalized to [0, 1).
    The probability intervals become less evenly distributed as the base increases.

    Args:
        n (int): Number of intervals.
        base (float): The base of the exponential (>1). Default is 2.
        A larger base will make the probability less evenly distributed across intervals.

    Returns:
        list[tuple[float, float]]: List of intervals [start, end).
    """
    weights = [base**-i for i in range(n)]
    total = sum(weights)
    probs = [w / total for w in weights]

    intervals = []
    current = 0.0
    for p in probs:
        next_val = current + p
        intervals.append((current, next_val))
        current = next_val
    
    return intervals

def get_n():
    """
    This function generates a random number and uses exponentially decreasing intervals 
    to return one of five possible values: 5, 6, 7, 4, or 8. Each value corresponds 
    to an interval with a specific probability determined by an exponential distribution.
    
    The probability distribution is based on 5 intervals whose lengths are computed 
    using an exponential decay formula with base 2. As the intervals increase, the 
    probability of falling within a given interval decreases.

    - Interval 1: Highest probability (38.4%) -> Returns 5
    - Interval 2: Moderate probability (25.6%) -> Returns 6
    - Interval 3: Moderate probability (17.1%) -> Returns 7
    - Interval 4: Low probability (11.4%) -> Returns 4
    - Interval 5: Very low probability (7.5%) -> Returns 8
    
    The probabilities are determined by the exponential decay, where the first 
    interval is the widest (highest probability) and the subsequent intervals get narrower 
    (lower probability).

    Returns:
        int: One of the following values based on which interval the random number falls into:
            5, 6, 7, 4, or 8.
    """

    intervals = get_exponential_intervals(5, base=1.8)
    random_number = random.random()

    for i, (start, end) in enumerate(intervals, start=1):
        if start <= random_number < end:
            return {
                1: 5,
                2: 6,
                3: 4,
                4: 7,
                5: 8
            }.get(i, None)
        
def main():
    # Retrieve arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_exams", type=int, default=1, help="Specify the number of exams (must be a positive integer).")
    parser.add_argument("--difficulty", type=str, default="random", help="Choose the difficulty level from the following options: 'easy', 'medium', 'hight', 'random'.")
    parser.add_argument("--exam", type=str, default="Artificial Intelligence Exam", help="Specify the title.")
    parser.add_argument("--date", type=str, default=datetime.now().strftime('%d-%m-%Y'), help=f"Specify the date in format dd-mm-yyyy (e.g., {datetime.now().strftime('%d-%m-%Y')}).")
    parser.add_argument("--consistency", type=str, default="m", help="Specifies whether or not solutions should have consistency (y=yes, n=no, m=mixed)")
    
    args = parser.parse_args()

    n_exams = args.n_exams
    difficulty = args.difficulty
    exam = args.exam
    date = args.date
    consistency = args.consistency

    # Check arguments 
    if args.n_exams <= 0:
        print("Error: n_exams must be a positive integer.")
        return    
    
    if args.difficulty not in ['easy', 'medium', 'high', 'random']:
        print("Error: difficulty must be one of 'easy', 'medium', 'hard', 'random'.")
        return
    
    if args.consistency not in ['y', 'n', 'm']:
        print("Error: consistency must be one of 'y', 'n', 'm'.")
        return
    
    try:
        if date is not None:
            datetime.strptime(date, '%d-%m-%Y')
    except ValueError:
        print(f"Error: date must be in format dd-mm-yyyy (e.g., {datetime.now().strftime('%d-%m-%Y')}).")
        return
    
    # Generate folder exams
    os.makedirs("../exams", exist_ok=True)
    
    # Backup sources
    source_folder_s = '../sources'
    backup_folder_s = '../.sources_backup'

    if os.path.exists(backup_folder_s):
        shutil.rmtree(backup_folder_s)

    os.rename(source_folder_s, backup_folder_s)
    os.makedirs(source_folder_s)

    # Backup exports
    source_folder_e = '../exports'
    backup_folder_e = '../.exports_backup'

    if os.path.exists(backup_folder_e):
        shutil.rmtree(backup_folder_e)

    os.rename(source_folder_e, backup_folder_e)
    os.makedirs(source_folder_e)

    # Create Results folder
    folder = create_results_folder('../exams', "results")

    # start generating
    for i in range(0, n_exams):
        # Generate n
        n = get_n()
        nodes_list = NodesList(n)

        count = -1
        while True:
            try:
                count = count + 1
                
                if count % 15 == 0: # If after 15 attempts I still haven't found an acceptable graph, I'll generate a new n.
                    # Generate n
                    n = get_n()
                    nodes_list = NodesList(n)
                
                nodes = nodes_list.get_names()
                edges = []

                for node in nodes[:-1]: # Each node (except G) must be connected to at least 2 nodes

                    param = 5*n/8-2 # (4, 0.5) -> (8, 3)
                    intervals = get_exponential_intervals(3, base=param)
                    random_number = random.random()

                    for j, (start, end) in enumerate(intervals, start=1):
                        if start <= random_number < end:
                            random_value = j

                    connected_nodes = random.sample([n for n in nodes if n != node], random_value)
                    for connected_node in connected_nodes:
                        # Add the edge in one of the two directions. 
                        # If one of the nodes is A, it's more likely that the edge starts from A."
                        if node == 'A':
                            if random.random() > 0.05:
                                edges.append((node, connected_node))
                            else:
                                edges.append((connected_node, node))
                        elif connected_node == 'A':
                            if random.random() > 0.95:
                                edges.append((node, connected_node))
                            else:
                                edges.append((connected_node, node))
                        elif random.random() > 0.5:
                            edges.append((node, connected_node))
                        else:
                            edges.append((connected_node, node))
                
                # Create the graph
                G = nx.DiGraph()
                G.add_nodes_from(nodes)
                G.add_edges_from(edges)

                ##### EDGE REQUIREMENTS #####

                # V -> to be verified in finite graph

                # 1. G cannot be connected only to A (V)
                # 2. G can only receive edges
                # 3. The average of number of edges per node is inversely proportional to n
                # 4. Every node (except G) must have outgoing edges (V)
                # 5. Every node (except A) must have incoming edges (V)
                # 6. If a node has only one incoming and one outgoing edge, it cannot involve the same node (V)
                # 7. The number of edges must be greater than N (V)
                # 8. Every node must be involved in at least one solution (to resolve deadlocks) (V)
                # 9. There must be at least 3 possible solutions (V)

                ##### 1 #####
                if len(G.in_edges('G')) == 1 and G.has_edge('A', 'G'):
                    continue

                ##### 2 #####
                L=0.95
                edges_to_invert = [(u, v) for u, v in G.edges() if u == 'G']
                for u, v in edges_to_invert:
                    G.remove_edge(u, v)
                    if random.random() > L*n/4-L:
                        G.add_edge(v, u)

                ##### 4 #####
                if any(G.out_degree(node) == 0 for node in G.nodes() if node != 'G'):
                    continue

                ##### 5 #####
                if any(G.in_degree(node) == 0 for node in G.nodes() if node != 'A'):
                    continue

                ##### 6 #####
                if any(
                    G.in_degree(node) == 1 and G.out_degree(node) == 1 and
                    list(G.in_edges(node))[0][0] == list(G.out_edges(node))[0][1]
                    for node in G.nodes()
                ):
                    continue

                ##### 7 #####
                if G.number_of_edges() <= n:
                    continue

                ##### 8 #####
                start = 'A'
                goal = 'G'

                all_paths = list(nx.all_simple_paths(G, source=start, target=goal))

                used_edges = set()
                for path in all_paths:
                    for u, v in zip(path, path[1:]):
                        used_edges.add((u, v))

                all_edges = set(G.edges())
                if all_edges != used_edges:
                    continue

                ##### 9 #####
                # check that the ratio between all possible solutions / arrows arriving at G is greater than param
                # param calculated linearly
                # line between points (4, 2) (8, 1.5)
                if(len(all_paths)/len(G.in_edges('G'))<(-0.125*n+2.5)):
                    continue

                ##### PATH REQUIREMENTS #####
                # 1.1 The path A->G has a high cost
                # 1.2 The second edge of the shortest path has a medium-high cost
                # 1.3 The edges in the longest path have a low cost
                # 1.4 All other edges have a low cost
                # 2. G, on the other hand, must be able to be reached at all nodes (V)
                    # This is verified in the Dijkstra algorithm (if it doesn't reach, it outputs infinity)
                    # This ensures there is no error later, but doesn't eliminate all situations with unnecessary nodes

                ##### 1 #####
                longest_path = max(all_paths, key=len)

                edges_in_longest_path = set()
                for u, v in zip(longest_path, longest_path[1:]):
                    edges_in_longest_path.add((u, v))

                edges_with_costs = []

                shortest_path = min(all_paths, key=len)

                second_edge_in_shortest_path = None
                if len(shortest_path) >= 2:
                    second_edge_in_shortest_path = shortest_path[1]

                for u, v in G.edges():
                    if u == 'A' and v == 'G':
                        cost = random.randint(12, 18)  # Special case A->G
                    elif (u, v) == second_edge_in_shortest_path:
                        cost = random.randint(9, 12)   # Second edge of the shortest path
                    elif (u, v) in edges_in_longest_path:
                        cost = random.randint(2, 7)    # Edge in the longest path
                    else:
                        cost = random.randint(5, 9)    # All other edges
                    edges_with_costs.append((u, v, cost))

                ##### 2 #####
                graph = defaultdict(list) # Build the inverted graph
                for u, v, cost in edges_with_costs:
                    graph[v].append((u, cost))

                goal = 'G'
                distances = dijkstra_from_goal(graph, goal)

                should_continue = False

                for node in sorted(distances):
                    if distances[node] == float('inf'):
                        should_continue = True
                        break

                if should_continue:
                    continue

                heuristics = {}

                # Calculate all except G
                for node in sorted(distances): 
                    if node == 'G':
                        continue  # lo gestiamo alla fine

                    max_distance = distances[node]
                    if max_distance == float('inf') or max_distance == 0:
                        continue

                    mid_point = max_distance / 2

                    if random.random() < 0.6:
                        # Upper half
                        heuristic = random.randint(max(1, int(mid_point)), int(max_distance))
                    else:
                        # Lower half
                        heuristic = random.randint(1, max(1, int(mid_point)))

                    heuristics[node] = heuristic

                # Calculate G
                heuristics['G'] = 0

                # Verify consistence
                # I just verify it now beacause i need heuristics
                if consistency == 'y' and not check_consistency(edges_with_costs, heuristics):
                    continue
                if consistency == 'n' and check_consistency(edges_with_costs, heuristics):
                    continue

                # Build yaml
                yaml_str = build_yaml(exam, date, heuristics, edges_with_costs)

                # Verify number of expansions
                config = yaml.safe_load(yaml_str)
                search_data = config['exercises']['search']
                search = Search(**search_data)
                tree = nx.DiGraph()
                val = search.graph.nodes[search.source]['value']
                tree.add_node(0, name=search.source, level=1, cost=0.0, value=val, heuristic=f'f=0.0+{val}={val}')
                outcome, expansions = search.a_star(tree=tree, visited={n: False for n in search.graph.nodes})

                # print(outcome, expansions) -> i can use it for statitics

                if outcome:
                    if difficulty == 'easy' and (expansions < 3 or expansions > 4):
                        continue
                    if difficulty == 'medium' and (expansions < 5 or expansions > 7):
                        continue
                    if difficulty == 'high' and (expansions < 8 or expansions > 11):
                        continue
                else:
                    continue

                with open("../sources/file.yaml", "w") as f:
                    f.write(yaml_str)

                result = subprocess.run(
                    ["python", "main.py"],
                    capture_output=True,
                    text=True,
                    cwd="../scripts"
                )

                if result.returncode != 0:
                    continue

                os.makedirs(folder, exist_ok=True)

                subfolder_path = os.path.join(folder, f"result_{i+1}")
                os.makedirs(subfolder_path, exist_ok=False)

                # Fill the Result
                copy_contents(source_folder_s, subfolder_path)
                copy_contents(source_folder_e, subfolder_path)
            except Exception as e:
                continue
            print(f"Generate {i+1}/{n_exams} in {subfolder_path}")
            break
    
    # Backup sources
    restore_backup(source_folder_s, backup_folder_s)
    
    # Backup extends
    restore_backup(source_folder_e, backup_folder_e)

if __name__ == "__main__":
    main()

