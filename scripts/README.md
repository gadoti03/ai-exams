# Exam Graph Generator

This tool allows the creation, generation, and extraction of search problems (state-space graphs) for Artificial Intelligence exams.  
It provides both a graphical editor and automatic generation capabilities, and supports importing graphs from images.

---

## Setup Instructions

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

---


## TASK 1 — Manual Exam Solution Creation

### Launch Jupyter interface:
```bash
cd ui
jupyter lab
```

Open `generate_solution.ipynb`.

### Step-by-step:

1. **Enter Exam Name and Date**  
   → Fields: `Exam:` and `Date:`  
   Used in the YAML header and file naming.

2. **Insert Node Names**  
   → Field: `Nodes:`  
   Format: space, comma or underscore-separated (e.g., `A B C`, or `A,B,C`).  
   Automatically updates the `Heuristic` and `Arcs` sections.

3. **Assign Heuristic Values**  
   Each node must have a numeric heuristic value.

4. **(Optional) Assign Custom Order**  
   Used only if "order of nodes" is selected as tie-breaker.  
   Each node gets a unique order number.

5. **Define Edges Between Nodes**  
   In the `Arcs` section, set the cost for each direction (e.g., `A → B` and `B → A`).  
   Leave empty to ignore that direction.

6. **Select Source and Destination Nodes**  
   These are dynamically populated based on the inserted nodes.

7. **(Optional) Tweak Visual Parameters**  
   Graph ratio, level ratio, etc. — affect only visualization.

8. **Choose Tie-Breaking Strategy for f(n)**  
   Options:
   - Alphabetical order
   - Manual node order

9. **Click “Generate Exam Solution”**  
   This will:
   - Save the graph in `../sources/file.yaml`
   - Trigger the `main.py` generator in `../scripts/`
   - Export a `.docx` to `../exports/`

### Common Errors

- Nodes without heuristic values  
- Non-numeric arc costs  
- Missing node orders (if required)  
- Source or destination node not selected

### Minimal Example

- Nodes: `A B C`  
- Heuristics: `A: 5`, `B: 3`, `C: 0`  
- Arcs:  
  - A → B: 1, B → A: 1  
  - B → C: 2, C → B: 2  
- Source: `A`  
- Destination: `C`  
- Tie-breaker: alphabetical order

---

## TASK 2 — Random Exam Generation

This module generates search problems with varying difficulty and structure.

### How to Use

1. **Insert exam name** (e.g., `"AI - July Session"`)
2. **Select the exam date** (or use today’s)
3. **Choose number of versions** (1–20)
4. **Pick difficulty**
   - Easy: 3–4 expansions
   - Medium: 5–7
   - High: 8–11
   - Random: varies by instance
5. **Choose consistency**
   - Yes: logically consistent problems
   - No: fully random
   - Mixed: semi-random

6. **Click "Generate Exams"**

This launches `generate_exams.py`, which generates:
- One directory per session inside `exams/`
- One folder per version with:
  - `graph.yaml`: the graph structure
  - `exam.docx`: formatted exam with the problem

---

## TASK 3 — Extract Graph from Image

Extract graph structure directly from a diagram (e.g., in a solution `.docx` file).

### Usage

```bash
cd scripts
python3 extract_graph_from_image.py <image_path>
```

### Inputs
- The image should represent a node-link diagram (state-space graph).
- You can find sample inputs in the `exampleGraphs/` folder.

### Outputs
- Extracted YAML saved to: `sources/`
- `.docx` version exported to: `exports/`

---

## Outputs Summary

- `sources/`: YAML representations of graphs
- `exports/`: Word documents of exams or solutions
- `exams/`: Auto-generated exam sessions, with per-exam folders

---

## Requirements

See `requirements.txt` for full list.  
Core libraries include: `networkx`, `ipywidgets`, `matplotlib`, `docx`, `pillow`, `scikit-image`, etc.

---

## Questions?

Open an issue or contact the maintainer.
