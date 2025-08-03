class Arc:
    def __init__(self, node_1, node_2, value_1=None, value_2=None):
        """
        Inizializza un arco orientato tra due nodi, con valori opzionali in entrambe le direzioni.

        :param node_1: Nodo di partenza.
        :param node_2: Nodo di arrivo.
        :param value_1: Valore associato all'arco da node_1 a node_2.
        :param value_2: Valore associato all'arco da node_2 a node_1 (opzionale, per archi bidirezionali).
        """
        self.node_1 = node_1
        self.node_2 = node_2
        self.value_1 = value_1
        self.value_2 = value_2

    def __repr__(self):
        return (f"Arc(node_1='{self.node_1}', node_2='{self.node_2}', "
                f"value_1={self.value_1}, value_2={self.value_2})")

    def has_equal_nodes(self, other_arc):
        """
        Verifica se i nodi (node_1, node_2) corrispondono a quelli di un altro arco.
        :param other_arc: Un altro oggetto Arc.
        :return: True se i nodi sono uguali, False altrimenti.
        """
        return self.node_1 == other_arc.node_1 and self.node_2 == other_arc.node_2

    def has_equal_nodes_params(self, node_1, node_2):
        """
        Verifica se i nodi corrispondono ai parametri forniti.
        :param node_1: Nodo di partenza.
        :param node_2: Nodo di arrivo.
        :return: True se i nodi sono uguali, False altrimenti.
        """
        return self.node_1 == node_1 and self.node_2 == node_2


class ArcList:
    def __init__(self):
        """Inizializza una lista vuota di archi."""
        self.arcs = []

    def add_arc(self, arc):
        """
        Aggiunge un arco alla lista, evitando duplicati.
        :param arc: Oggetto Arc da aggiungere.
        """
        if not any(a.has_equal_nodes(arc) for a in self.arcs):
            self.arcs.append(arc)

    def remove_arc(self, arc):
        """
        Rimuove un arco dalla lista.
        :param arc: Oggetto Arc da rimuovere.
        """
        self.arcs = [a for a in self.arcs if not a.has_equal_nodes(arc)]

    def get_arc(self, node_1, node_2):
        """
        Restituisce l'arco con nodi specificati, se esiste.
        :param node_1: Nodo di partenza.
        :param node_2: Nodo di arrivo.
        :return: Oggetto Arc o None.
        """
        for arc in self.arcs:
            if arc.has_equal_nodes_params(node_1, node_2):
                return arc
        return None

    def get_arcs(self):
        """Restituisce la lista completa degli archi."""
        return self.arcs

    def get_arcs_values_str(self):
        """
        Restituisce una stringa formattata con gli archi e i loro valori,
        se presenti almeno da una direzione.
        :return: Stringa degli archi formattata oppure None se vuota.
        """
        string = ""
        for arc in self.arcs:
            if arc.value_1 is not None and arc.value_1 != "":
                string += " " * 6 + "- [ " + arc.node_1 + ", " + arc.node_2 + ", " + str(arc.value_1) + " ]\n"
            if arc.value_2 is not None and arc.value_2 != "":
                string += " " * 6 + "- [ " + arc.node_2 + ", " + arc.node_1 + ", " + str(arc.value_2) + " ]\n"
        return string if string else None

    def __len__(self):
        """Restituisce il numero di archi nella lista."""
        return len(self.arcs)

    def __iter__(self):
        """Permette l'iterazione sugli archi."""
        return iter(self.arcs)

    def __str__(self):
        """Restituisce una rappresentazione in stringa della lista di archi."""
        return ', '.join([repr(arc) for arc in self.arcs])
