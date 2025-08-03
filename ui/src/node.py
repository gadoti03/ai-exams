class Node:
    def __init__(self, name, value=0):
        """
        Inizializza un nodo con un nome e un valore (intero), più un campo 'ord' opzionale.

        :param name: Il nome del nodo.
        :param value: Un valore intero associato al nodo (default: 0).
        """
        self.name = name
        self.value = value
        self.ord = ""

    def __str__(self):
        return f"Node(name: {self.name}, value: {self.value}, ord: {self.ord})"

    def __repr__(self):
        return f"Node(name={self.name}, value={self.value}, ord: {self.ord})"

    def get_name(self):
        """Restituisce il nome del nodo."""
        return self.name

    def get_value(self):
        """Restituisce il valore associato al nodo."""
        return self.value

    def get_ord(self):
        """Restituisce la posizione di priorità (ord) del nodo."""
        return self.ord


class NodeList:
    def __init__(self):
        """Inizializza una lista vuota di nodi."""
        self.nodes = []

    def add_node(self, node):
        """Aggiunge un nodo alla lista, se non è già presente (per nome)."""
        if not any(n.name == node.name for n in self.nodes):
            self.nodes.append(node)

    def remove_node(self, node_name):
        """Rimuove un nodo dalla lista dato il suo nome."""
        self.nodes = [n for n in self.nodes if n.name != node_name]

    def get_node(self, node_name):
        """Restituisce il nodo con il nome specificato, oppure None se non esiste."""
        for node in self.nodes:
            if node.name == node_name:
                return node
        return None

    def get_value(self, node_name):
        """Restituisce il valore associato a un nodo dato il suo nome."""
        node = self.get_node(node_name)
        return node.value if node else None

    def update_node_value(self, node_name, new_value):
        """Aggiorna il valore di un nodo dato il suo nome."""
        node = self.get_node(node_name)
        if node:
            node.value = new_value

    def contains_name(self, name: str) -> bool:
        """Controlla se esiste un nodo con il nome specificato."""
        return any(node.name == name for node in self.nodes)

    def get_list_names(self):
        """Restituisce una lista dei nomi di tutti i nodi."""
        return [node.name for node in self.nodes]

    def get_nodes_values_str(self):
        """
        Restituisce una stringa formattata con i nomi dei nodi e i rispettivi valori.
        Restituisce None se uno dei valori è mancante.
        """
        string = ""
        for node in self.nodes: 
            if node.value is not None and node.value != "":
                string += " " * 6 + node.name + ": " + str(node.value) + "\n"
            else:
                return None
        return string

    def get_nodes_ords_str(self) -> str | None:
        """
        Restituisce una stringa formattata con i nomi dei nodi e i rispettivi ord.
        Restituisce None se uno degli ord è mancante.
        """
        string = "    ords:\n"
        for node in self.nodes: 
            if node.ord is not None and node.ord != "":
                string += " " * 6 + node.name + ": " + str(node.ord) + "\n"
            else:
                return None
        return string

    def validate(self) -> bool:
        """
        Verifica che tutti i nodi abbiano un valore 'ord' valido:
        - Deve essere un intero compreso tra 1 e n (inclusi).
        - Tutti i valori devono essere univoci.

        :return: True se tutti i nodi hanno un 'ord' valido e unico, False altrimenti.
        """
        try:
            ords = [int(node.ord) for node in self.nodes]
        except (ValueError, TypeError):
            return False
        
        n = len(self.nodes)
        return sorted(ords) == list(range(1, n + 1))

    def __len__(self):
        """Restituisce il numero di nodi nella lista."""
        return len(self.nodes)

    def __iter__(self):
        """Permette l'iterazione sui nodi."""
        return iter(self.nodes)

    def __str__(self):
        """Restituisce una rappresentazione in stringa della lista di nodi."""
        return ', '.join([str(node) for node in self.nodes])
