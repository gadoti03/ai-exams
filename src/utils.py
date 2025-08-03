import cv2
import numpy as np
import matplotlib.pyplot as plt
import pytesseract
import math

# Classes and functions for extract_graph_from_image.py

#################################
### Classes #####################
#################################

class Node:
    def __init__(self, name: str, x: int, y: int, r: int, heuristic: int = None):
        self.name = name
        self.x = x
        self.y = y
        self.r = r
        self.heuristic = heuristic

    def __repr__(self):
        return f"Node(name='{self.name}', x={self.x}, y={self.y}, r={self.r}, h={self.heuristic})"

class Arc:
    def __init__(self, node1, node2, group, direction=None, value=None, estrem1 = None, estrem2 = None):
        """
        direction: 
            0 -> node1 --> node2
            1 -> node1 <-- node2
            2 -> node1 <-> node2
        value: costo dell'arc
        """
        self.node1 = node1
        self.node2 = node2
        self.group = group
        self.direction = direction
        self.value = value
        self.estrem1 = estrem1
        self.estrem2 = estrem2

    def __repr__(self):
        if self.direction == 0:
            arrow = "->"
        elif self.direction == 1:
            arrow = "<-"
        elif self.direction == 2:
            arrow = "<->"
        else:
            arrow = "?"
        return f"{self.node1.name} {arrow} {self.node2.name} [cost: {self.value}] [estremes: {self.estrem1}, {self.estrem2}]"

#################################
### Functions ###################
#################################

def compute_angle(x1, y1, x2, y2):
    # If we are close to ±pi/2 I return pi/2
    if abs(x1 - x2)<=10:
        return (math.pi / 2)
    return math.atan((y2 - y1) / (x2 - x1))

def distance(p1, p2):
    # Measure the distance between 2 points
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def valuate_q(angle, line):
    x1, y1, x2, y2 = line
    # Problem: if the line is vertical, q becomes huge → hard to manage
    if abs(abs(angle) - (np.pi / 2)) <= (np.pi / 36):  # error margin of 5 degrees
        return x1
    return y1 - math.tan(angle) * x1

def generate_arc(group, nodeslist, tolleranza=150):
    estremi_trovati = set()

    # Algorithm for grouping lines
    for (x1, y1, x2, y2) in group["lines"]:
        for nodo in nodeslist:
            centro = (nodo.x, nodo.y)
            raggio_effettivo = nodo.r + tolleranza

            if distance((x1, y1), centro) <= raggio_effettivo:
                estremi_trovati.add(nodo)
            if distance((x2, y2), centro) <= raggio_effettivo:
                estremi_trovati.add(nodo)

        if len(estremi_trovati) >= 2:
            break

    if len(estremi_trovati) != 2:
        print(f"Warning: non-unique extremes found: {estremi_trovati}")

    estrmes = list(estremi_trovati)

    # Generation of the arc
    arc = Arc(estrmes[0], estrmes[1], group)
    find_arc_extremes(arc)
    return arc

def find_arc_extremes(arc):
    '''
    find the coordinates of the two extreme points of the arc
    '''
    points = []
    for line in arc.group["lines"]:
        x1, y1, x2, y2 = line
        points.append((x1,y1))
        points.append((x2,y2))
    max_dist = 0
    point_pair = (None, None)

    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = distance(points[i], points[j])
            if d > max_dist:
                max_dist = d
                point_pair = (points[i], points[j])

    arc.estrem1 = point_pair[0]
    arc.estrem2 = point_pair[1]

def update_arc_direction(arc, tolerance=15):
    """
    Updates the 'direction' attribute of an Arc using the arc's endpoints (estrem1, estrem2)
    and their distances from node1 and node2.
    
    direction values:
        0 -> node1 --> node2
        1 -> node1 <-- node2
        2 -> node1 <-> node2
        None -> undetermined
    """
    node1 = arc.node1
    node2 = arc.node2

    r1 = node1.r + tolerance
    r2 = node2.r + tolerance

    p1 = arc.estrem1
    p2 = arc.estrem2

    # Calculate the distances of the two ends from each node
    d1_p1 = distance((node1.x, node1.y), p1)
    d1_p2 = distance((node1.x, node1.y), p2)
    d2_p1 = distance((node2.x, node2.y), p1)
    d2_p2 = distance((node2.x, node2.y), p2)

    # Check if p1/p2 are close enough to one of the two nodes
    found_0 = False  # node1 --> node2
    found_1 = False  # node1 <-- node2

    if d1_p1 <= r1 or d1_p2 <= r1:
        found_0 = True
    if d2_p1 <= r2 or d2_p2 <= r2:
        found_1 = True

    # Determine the final direction
    if not found_0 and not found_1:
        arc.direction = 2
    elif found_0:
        arc.direction = 0
    elif found_1:
        arc.direction = 1
    else:
        arc.direction = None

def draw_arc_extremes(img, arcs, color=(255, 0, 255), radius=6):
    """
    Draws the endpoints (estrem1, estrem2) of each arc on the `img`.

    Args:
        img: the image to draw on (modified in place)
        arcs: list of Arc objects, each with attributes estrem1 and estrem2
        color: color of the circles to draw (default is magenta)
        radius: radius of the circles
    """
    for arc in arcs:
        if arc.estrem1 is not None:
            pt1 = tuple(np.round(arc.estrem1).astype(int))
            cv2.circle(img, pt1, radius, color, -1)
        if arc.estrem2 is not None:
            pt2 = tuple(np.round(arc.estrem2).astype(int))
            cv2.circle(img, pt2, radius, color, -1)

def draw_circle_along_arc(img, arc, radius=25, color=(0, 255, 0), perc=0.65):
    """
    Draws one or two circles along the arc to indicate direction,
    placing them at 'perc' of the distance between the centers of the two nodes.
    """
    p1 = arc.estrem1
    p2 = arc.estrem2
    if p1 is None or p2 is None:
        return []

    # Node's center
    center1 = np.array([arc.node1.x, arc.node1.y], dtype=np.float32)
    center2 = np.array([arc.node2.x, arc.node2.y], dtype=np.float32)

    # Calculate the position per cent of the distance between the two nodes
    def draw_direction(from_center, to_center):
        pos = from_center + perc * (to_center - from_center)
        cv2.circle(img, tuple(pos.astype(int)), radius, color, 2)
        return pos

    circle_positions = []

    if arc.direction == 0:
        # Direction from node1 to node2
        circle_positions.append(draw_direction(center1, center2))

    elif arc.direction == 1:
        # Direction from node2 to node1
        circle_positions.append(draw_direction(center2, center1))

    elif arc.direction == 2:
        # Both directions
        circle_positions.append(draw_direction(center1, center2))
        circle_positions.append(draw_direction(center2, center1))

    return circle_positions


def crop_circle_and_ocr(img, center, r, arc):
    center = center[0]
    x, y = int(center[0]), int(center[1])
    r = int(r * 0.9) # light inner margin

    # Circular mask on white background
    full_mask = np.zeros((2*r, 2*r), dtype=np.uint8)
    cv2.circle(full_mask, (r, r), r, 255, -1)

    # ROI coordinates in the image
    h, w = img.shape[:2]
    x1, y1 = max(0, x - r), max(0, y - r)
    x2, y2 = min(w, x + r), min(h, y + r)
    roi = img[y1:y2, x1:x2].copy()

    # Fit mask if ROI is cut off by image edges
    mask = full_mask.copy()
    dy1 = r - (y - y1)
    dy2 = r + (y2 - y)
    dx1 = r - (x - x1)
    dx2 = r + (x2 - x)
    mask = mask[dy1:dy2, dx1:dx2]

    # First filter: keep only pixels inside the circle, outside becomes white
    white_background = np.ones_like(roi, dtype=np.uint8) * 255
    roi_after_circle_mask = np.where(mask[:, :, None] == 255, roi, white_background)

    # Second filter: keep only dark non-green pixels
    roi_gray = cv2.cvtColor(roi_after_circle_mask, cv2.COLOR_BGR2GRAY)
    threshold_dark = 50
    mask_dark = roi_gray <= threshold_dark

    b, g, r = cv2.split(roi_after_circle_mask)

    mask_green = (g > r + 20) & (g > b + 20)

    mask_final = mask_dark & (~mask_green)

    # Apply final mask
    roi_masked = np.where(mask_final[:, :, None], roi_after_circle_mask, white_background)

    # Ruota in base all'angolo contenuto in arc
    angle_deg = np.degrees(arc.group['angle'])  # rad → deg
    center_rot = (roi_masked.shape[1] // 2, roi_masked.shape[0] // 2)
    M = cv2.getRotationMatrix2D(center_rot, angle_deg, 1.0)
    roi_rotated = cv2.warpAffine(
        roi_masked, M,
        (roi_masked.shape[1], roi_masked.shape[0]),
        borderValue=(255, 255, 255)  # bianco per consistenza
    )

    # OCR configured for numbers only
    config = '--psm 6 -c tessedit_char_whitelist=0123456789'
    text = pytesseract.image_to_string(roi_rotated, config=config)

    '''
    # Image of single cost of the arc

    plt.figure(figsize=(3, 3))
    plt.imshow(cv2.cvtColor(roi_rotated, cv2.COLOR_BGR2RGB))
    plt.title(f"OCR: {text.strip()}")
    plt.axis('off')
    plt.show()

    '''

    return text.strip()

def generate_yaml(nodesList, arcsList):
    '''
    generating the yaml suitable for main.py
    '''
    nodes = []

    for node in nodesList:
        nodes.append(6*" " + node.name + ": " + str(node.heuristic)+"\n")

    nodes = sorted(nodes)

    yaml_content = '''exam: Artificial Intelligence Exam
date: 22-07-2025
exercises:
  search:
    source: A
    destination: G
    tiebreaker: alphabetical order
    nodes:
'''
    for el in nodes:
        yaml_content = yaml_content + el
    yaml_content = yaml_content + "    arcs:\n"

    arcs = []
    for arc in arcsList:
        if arc.direction == 0 or arc.direction == 2:
            arcs.append([arc.node1.name, arc.node2.name, str(arc.value)])
        if arc.direction == 1 or arc.direction == 2:
            arcs.append([arc.node2.name, arc.node1.name, str(arc.value)])
    arcs = sorted(arcs, key=lambda x: x[0])

    for el in arcs:
        yaml_content = yaml_content + " "*6 + "- [" + el[0] + ", " + el[1] + ", " + el[2] + "]\n"

    yaml_content = yaml_content + '''    graph_ratio: 1.0
    level_ratio: 7.0
    label_offset: 0.13
    heuristic_offset: 0.1'''
    return yaml_content