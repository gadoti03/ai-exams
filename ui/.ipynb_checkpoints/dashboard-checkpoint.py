import ipywidgets as widgets
from IPython.display import display
import yaml
import numpy as np

# Funzione per creare il YAML
def generate_yaml(exam_name, exam_date, nodes, arcs, graph_ratio, level_ratio, label_offset, heuristic_offset):
    data = {
        'exam': exam_name,
        'date': exam_date,
        'exercises': {
            'search': {
                'source': nodes[0],
                'destination': nodes[-1],
                'nodes': {node: 15 for node in nodes},
                'arcs': arcs,
                'graph_ratio': graph_ratio,
                'level_ratio': level_ratio,
                'label_offset': label_offset,
                'heuristic_offset': heuristic_offset
            }
        }
    }
    # Creazione del file YAML
    with open('exam_data.yaml', 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

    print("YAML file created successfully!")

# Widget di input per i dati principali
exam_name_input = widgets.Text(value='Artificial Intelligence Exam', description='Exam:')
exam_date_input = widgets.Date(value=pd.to_datetime('2025-06-01'), description='Date:')

# Widget per inserire nodi e archi
node_input = widgets.Text(value='A, B, C, D, F, G', description='Nodes (comma-separated):')
arc_input = widgets.Text(value='[ A, B, 10 ], [ A, C, 12 ], [ B, C, 5 ], [ B, D, 8 ], [ B, F, 3 ], [ C, D, 5 ], [ C, G, 11 ], [ D, G, 6 ], [ F, G, 7 ]', description='Arcs:')
graph_ratio_input = widgets.FloatSlider(value=1, min=0, max=5, step=0.1, description='Graph Ratio:')
level_ratio_input = widgets.FloatSlider(value=7, min=0, max=10, step=0.1, description='Level Ratio:')
label_offset_input = widgets.FloatSlider(value=0.13, min=0, max=1, step=0.01, description='Label Offset:')
heuristic_offset_input = widgets.FloatSlider(value=0.1, min=0, max=1, step=0.01, description='Heuristic Offset:')

# Bottone per generare il YAML
generate_button = widgets.Button(description="Generate YAML")
output = widgets.Output()

# Funzione che viene eseguita quando si clicca sul bottone
def on_generate_button_click(b):
    # Prendere i dati dagli input
    nodes = node_input.value.split(', ')
    arcs = eval(arc_input.value)  # Converte la stringa in una lista di tuple
    generate_yaml(exam_name_input.value, str(exam_date_input.value), nodes, arcs, graph_ratio_input.value, level_ratio_input.value, label_offset_input.value, heuristic_offset_input.value)

# Collegare il bottone al click
generate_button.on_click(on_generate_button_click)

# Visualizzare l'interfaccia
display(exam_name_input, exam_date_input, node_input, arc_input, graph_ratio_input, level_ratio_input, label_offset_input, heuristic_offset_input, generate_button, output)
