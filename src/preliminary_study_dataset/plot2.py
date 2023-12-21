import plotly.graph_objects as go
import json
import os
from collections import defaultdict
from PIL import Image
import re


# Script to install Plotly and Kaleido using pip3

import subprocess

# Function to install a package using pip3
def install(package):
    subprocess.check_call(["pip3", "install", package])

print("Checking if all the package are installed.")
# Install Plotly
install("plotly")

# Install Kaleido
install("kaleido")

def remove_bracketed_numbers(s):
    # This regex matches a left square bracket, followed by any number of digits, followed by a right square bracket
    return re.sub(r'\[\d+\]', '', s)

def read_json_files(folder_path):
    data = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            with open(os.path.join(folder_path, filename), 'r') as file:
                try:
                    json_content = json.load(file)
                    data.extend(json_content)
                except json.JSONDecodeError:
                    print(f"Error reading {filename}. File might not be a valid JSON.")
    return data
    
def format_right_label(label):
    return label.replace('_', ' ').capitalize()

def format_left_label(label):
    # Remove square brackets with numbers inside
    return re.sub(r'\[\d+\]', '', label).strip()

def prepare_sankey_data(json_data, left_order, right_order):
    links = defaultdict(lambda: defaultdict(int))
    additional_nodes = set()

    for item in json_data:
        type_error = item['type_error']
        pyre_detail = item['code_transform']
        if type_error not in left_order and type_error not in right_order:
            additional_nodes.add(type_error)
        if pyre_detail not in left_order and pyre_detail not in right_order:
            additional_nodes.add(pyre_detail)
        links[type_error][pyre_detail] += 1

    # Map the node names to indices based on the specified order, plus any additional nodes
    all_nodes = left_order + right_order + list(additional_nodes)
    node_indices = {name: idx for idx, name in enumerate(all_nodes)}

    # Convert links to source-target format
    source, target, value = [], [], []
    for src, targets in links.items():
        for tgt, count in targets.items():
            source.append(node_indices[src])
            target.append(node_indices[tgt])
            value.append(count)

    return source, target, value, all_nodes

def create_sankey_plot(source, target, value, nodes, output_file='figure2.pdf'):
    # Define node colors (you may want to customize this)
    node_colors = [
        'rgba(31, 119, 180, 0.8)',  # Blue
        'rgba(255, 127, 14, 0.8)',  # Orange
        'rgba(44, 160, 44, 0.8)',   # Green
        'rgba(214, 39, 40, 0.8)',   # Red
        'rgba(148, 103, 189, 0.8)', # Purple
    ]
    
    formatted_labels = [format_left_label(label) if label in left_order or label in "Inconsistent override [15]" else format_right_label(label) for label in nodes]
    
     # Extend the color list if there are more nodes than colors
    if len(nodes) > len(node_colors):
        node_colors.extend(node_colors * ((len(nodes) // len(node_colors)) + 1))


    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=15,
            line=dict(color="black", width=0.5),
            label=formatted_labels,
            color=node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        )
    )])

    #fig.update_layout(title_text="Figure 2 in the Paper", font_size=10)
    fig.write_image(output_file, format='pdf')
    print(f"\nPlot saved as {output_file}")

# Path to the folder containing JSON files
folder_path = '.'

# Define the custom order of nodes for left and right
left_order = [
    "Incompatible return type [7]",
    "Invalid type [31]",
    "Call error [29]",
    "Illegal annotation target [35]",
    "Incompatible parameter type [6]",
    "Incompatible variable type [9]",
    "Undefined attribute [16]",
    "Undefined Type [11]",
    "Unsupported operand [58]",
    "Redundant Cast [22]",
    "Inconsistent override [14]"
]

right_order = [
    "ADD_RETURN_VAL",
    "MODIFY_FUN_RETURN_VALUE",
    "MODIFY_FUN_RETURN_TYPE",
    "CASTING",
    "ADD_NONE_CHECK",
    "MODIFY_VAR_TYPE",
    "REMOVE_REANNOTATION",
    "OP_CHANGE",
    "REMOVE_TYPE",
    "MODIFY_FUN_PARAM_TYPE",
    "MODIFY_ISINSTANCE_CALL",
    "MODIFY_FUN_PARAM_VAL",
    "CREATE_NEW_VAR",
    "CALL_OTHER_METHOD",
    "REMOVE",
    "OTHER",
    "MODIFY_ATTR_TYPE"
]


# Read JSON data from files
json_data = read_json_files(folder_path)

# Prepare data for Sankey plot
source, target, value, nodes = prepare_sankey_data(json_data, left_order, right_order)

# Create and save Sankey plot
create_sankey_plot(source, target, value, nodes)

