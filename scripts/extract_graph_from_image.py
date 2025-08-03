import cv2
import numpy as np
import matplotlib.pyplot as plt
import pytesseract
import re
import math
import random
import os
import sys
import subprocess
import argparse

# --- Parse command-line arguments ---
parser = argparse.ArgumentParser(description="Extract graph data from image")
parser.add_argument("image_path", type=str, help="Path to the input image (e.g., grafi/grafico_4.png)")
args = parser.parse_args()

img_path = args.image_path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils import Node, Arc
from utils import compute_angle, generate_arc, valuate_q, update_arc_direction, draw_arc_extremes, draw_circle_along_arc, crop_circle_and_ocr, generate_yaml

# --- Load image ---
# img_path = "../exampleGraphs/grafico_4.png"
img = cv2.imread(img_path)
if img is None:
    raise FileNotFoundError(f"Image not found: {img_path}")
output = img.copy()

# --- Preprocessing ---
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (9, 9), 0)
_, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

# --- Find contours ---
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# List of nodes
nodesList = []
# List of arcs
arcsList = []

# --- 1: Analyze circles (nodes) ---
for i, cnt in enumerate(contours, 1):
    area = cv2.contourArea(cnt)
    if area < 1000:
        continue  # Ignore small contours that are unlikely to be nodes

    (x, y), radius = cv2.minEnclosingCircle(cnt)
    circle_area = np.pi * (radius ** 2)
    ratio = area / circle_area

    if 0.7 < ratio < 1.3:  # Check if the contour is roughly circular
        center = (int(x), int(y))
        radius = int(radius)

        # Reduce the radius to crop a smaller area inside the circle for OCR
        r_reduced = int(radius * 0.7)
        x1 = max(center[0] - r_reduced, 0)
        y1 = max(center[1] - r_reduced, 0)
        x2 = min(center[0] + r_reduced, img.shape[1]-1)
        y2 = min(center[1] + r_reduced, img.shape[0]-1)

        roi = gray[y1:y2, x1:x2]  # Region of interest for OCR

        # OCR configuration for single-line alphanumeric detection
        custom_config = r'--oem 3 --psm 7'
        text = pytesseract.image_to_string(roi, config=custom_config)
        text = re.sub(r'[^A-Z0-9]', '', text.strip().upper())  # Keep only uppercase letters and digits

        # Clear the original circle by drawing a white filled circle
        # cv2.circle(output, center, radius, (0, 255, 0), 2)  # (for debugging)
        # cv2.circle(output, center, 2, (0, 0, 255), 3)        # (for debugging)

        cv2.circle(output, center, radius+5, (255, 255, 255), thickness=-1)

        # Draw the detected text centered in the cleared circle
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        text_x = center[0] - text_width // 2
        text_y = center[1] + text_height // 2
        cv2.putText(output, text if text else "?", (text_x, text_y), font, font_scale, (0, 0, 0), thickness, lineType=cv2.LINE_AA)

        # Add the node to the list, using "?" if OCR fails
        node = Node(name=text if text else "?", x=center[0], y=center[1], r=radius)
        nodesList.append(node)

# --- 2: Analyze rectangles ---
for i, cnt in enumerate(contours, 1):
    area = cv2.contourArea(cnt)
    if area < 100:
        continue

    peri = cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

    if len(approx) == 4:
        x, y, w, h = cv2.boundingRect(approx)
        center_x, center_y = x + w // 2, y + h // 2

        # Reduce width and height to 80% to avoid borders
        w_reduced = int(w * 0.8)
        h_reduced = int(h * 0.8)

        x1 = max(center_x - w_reduced // 2, 0)
        y1 = max(center_y - h_reduced // 2, 0)
        x2 = min(center_x + w_reduced // 2, img.shape[1] - 1)
        y2 = min(center_y + h_reduced // 2, img.shape[0] - 1)

        roi = img[y1:y2, x1:x2]  # Use color image for OCR

        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
        # ??? I changed it to 6 because in some cases it doesn't work
        text = pytesseract.image_to_string(roi, config=custom_config)
        text = re.sub(r'[^0-9]', '', text.strip())

        if text.isdigit():
            heuristic = int(text)
            min_dist = float('inf')
            nearest_node = None
            for nodo in nodesList:
                dist = math.hypot(nodo.x - center_x, nodo.y - center_y)
                if dist < min_dist:
                    min_dist = dist
                    nearest_node = nodo
            if nearest_node:
                nearest_node.heuristic = heuristic

                # Optional annotation (can be removed if not needed)
                # Write the heuristic value near the node
                # cv2.putText(output, f"h={heuristic}", (nearest_node.x + 10, nearest_node.y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                # Remove the rectangle by slightly enlarging to also cover the borders
                padding = int(0 * max(w, h))  # 0% of the larger side
                x_pad1 = max(x - padding, 0)
                y_pad1 = max(y - padding, 0)
                x_pad2 = min(x + w + padding, img.shape[1] - 1)
                y_pad2 = min(y + h + padding, img.shape[0] - 1)

                cv2.rectangle(output, (x_pad1, y_pad1), (x_pad2, y_pad2), (255, 255, 255), thickness=-1)

        else:
            print(f"Rectangle: unrecognized text '{text}'")
        # Draw the rectangle contours
        # cv2.drawContours(output, [approx], -1, (255, 0, 0), 2)

# --- Image after reading circles (nodes) and rectangles (heuristics) ---
plt.figure(figsize=(10, 10))
plt.imshow(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
# plt.title("Image after reading circles (nodes) and rectangles (heuristics)")
plt.axis("off")
plt.show()

# Copy of output
img = output.copy()

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 50, 150, apertureSize=3)

# Retrieve the lines
lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=50, minLineLength=40, maxLineGap=10)

img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

plt.figure(figsize=(10, 10))
plt.imshow(img_rgb)

# --- Drawing all the lines in red ---
if lines is not None:
    for line in lines:
        x1, y1, x2, y2 = line[0]
        plt.plot([x1, x2], [y1, y2], color='red', linewidth=2)

# --- Image after recovering the lines ---

plt.axis('off')
# plt.title("Image after recovering the lines")
plt.axis("off")
plt.show()

# Group lines by angle and y-intercept (or x-intercept for vertical lines)

if lines is None:
    print("No lines found.")
else:
    angle_threshold = np.pi / 18  # about 10 degrees
    max_distance = 400  # maximum allowed distance between intercepts
    groups = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = compute_angle(x1, y1, x2, y2)

        matched = False
        for group in groups:
            # Check if the angle is close enough to an existing group
            if abs(angle - group["angle"]) < angle_threshold:
                for gx1, gy1, gx2, gy2 in group["lines"]:  # for each line in the group
                    current_points = x1, y1, x2, y2
                    group_points = gx1, gy1, gx2, gy2

                    # Check if the intercepts are close enough to be considered the same line
                    if abs(valuate_q(angle, current_points) - valuate_q(angle, group_points)) <= max_distance:
                        group["lines"].append((x1, y1, x2, y2))
                        matched = True
                        break  # go to the next line
                if matched:
                    break

        if not matched:
            # Create a new group for this line
            groups.append({"angle": angle, "lines": [(x1, y1, x2, y2)]})

# Generating arcs
for group in groups:
    arcsList.append(generate_arc(group, nodesList))

# Drawing arcs estremes
draw_arc_extremes(img, arcsList, color=(255, 0, 255), radius=6)

# Adding directions at arcs
for arc in arcsList:
    update_arc_direction(arc)

# Drawing the arcs with different colors
output_with_lines = img.copy()
for group in groups:
    color = tuple(random.randint(0, 255) for _ in range(3))
    for (x1, y1, x2, y2) in group["lines"]:
        cv2.line(output_with_lines, (x1, y1), (x2, y2), color, 2)

# --- Image after grouping the lines of the same arc ---
plt.figure(figsize=(10, 10))
plt.imshow(cv2.cvtColor(output_with_lines, cv2.COLOR_BGR2RGB))
# plt.title("Image after grouping the lines of the same arc")
plt.axis("off")
plt.show()

all_circle_positions = []  # list of all circle positions, for all arcs

for arc in arcsList:
    # Draw a circle along the arc on the output image
    circle_position = draw_circle_along_arc(output, arc)
    r = 25  # or the correct radius used inside draw_circle_along_arc

    # Perform OCR on the cropped region around the circle
    text = crop_circle_and_ocr(output, circle_position, r, arc)

    # Assign the extracted value to the arc
    arc.value = int(text)

# Convert the image from BGR (OpenCV format) to RGB (for matplotlib display)
img_rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

# --- Image after finding the cost of the arches ---
plt.figure(figsize=(10, 10))
plt.imshow(img_rgb)
plt.axis('off')
# plt.title('Image after finding the cost of the arches')
plt.show()

# --- Generate YAML file ---

output_dir = "../sources"
output_path = os.path.join(output_dir, "file.yaml")

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Generate YAML content from nodes and arcs
yaml_content = generate_yaml(nodesList, arcsList)

# Save the YAML content, overwriting the file if it exists
with open(output_path, "w") as f:
    f.write(yaml_content)

print(f"File saved at: {output_path}")

# --- Execute the external script ---
print("Running: main.py")
subprocess.run(["python3", "main.py"])
