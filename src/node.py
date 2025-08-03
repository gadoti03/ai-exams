class Node:
    def __init__(self, name):
        """
        Inizializza un nodo con un nome e una lista di archi vuota.
        
        Args:
            name (str): Il nome del nodo.
        """
        self.name = name
        self.edges = []  # Lista di archi, ogni arco è una tupla (altro nodo, value)

    def add_edge(self, other_node_name, value):
        """
        Aggiunge un arco al nodo.
        
        Args:
            other_node_name (str): Il nome dell'altro nodo a cui è collegato.
            value (float): Il valore dell'arco.
        """
        self.edges.append((other_node_name, value))

    def __repr__(self):
        """
        Restituisce una rappresentazione stringa del nodo e dei suoi archi.
        """
        return f"Node({self.name}, Edges: {self.edges})"


class NodesList:
    def __init__(self, n):
        """
        Crea una lista di nodi con nomi da A fino a G, ma con n-1 nodi in ordine alfabetico.
        
        Args:
            n (int): Il numero di nodi (tra 4 e 8).
        """
        if n < 4 or n > 8:
            raise ValueError("Il numero di nodi deve essere tra 4 e 8.")
        
        self.nodes = []
        
        # Creiamo i nodi da 'A' fino a (n-1) lettere
        j=0
        for i in range(n - 1):
            if i == 6:
                j = 1
            node_name = chr(65 + i+j)  # 'A' è il codice ASCII 65
            self.nodes.append(Node(node_name))
        
        # Aggiungiamo sempre 'G' come ultimo nodo
        self.nodes.append(Node('G'))

    def __repr__(self):
        """
        Restituisce una rappresentazione stringa della lista di nodi.
        """
        return f"NodesList({', '.join(str(node) for node in self.nodes)})"
    
    def get_names(self):
        """
        Restituisce una lista dei nomi dei nodi.
        """
        return [node.name for node in self.nodes]
