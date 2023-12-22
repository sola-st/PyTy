import json
import os
import matplotlib.pyplot as plt
from collections import Counter

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

def format_label(label):
    return label.replace('_', ' ').capitalize()
    
def plot_top_type_errors(json_data, top_n=7, output_file='figure4c.pdf'):
    # Extracting all 'type_error' values
    type_errors = [item['pyre_detail'] for item in json_data if item['pyre_detail'] != 'USE_ANOTHER_TYPE']

    # Counting occurrences of each type_error
    type_error_counts = Counter(type_errors)
    
    # Sorting errors first alphabetically, then by count
    sorted_errors = sorted(type_error_counts.items(), key=lambda x: (-x[1], x[0]))


    # Finding the top N type_errors
    top_type_errors = sorted_errors[1:top_n]
    #top_type_errors = type_error_counts.most_common(top_n)[1:]
    
    # Summing the counts of the remaining type_errors
    other_count = sum(count for _, count in type_error_counts.items() if _ not in dict(top_type_errors))

    # Adding "Other" category
    top_type_errors.append(("Others", 13)) # manual count after filtering

    # Separating the type errors and their counts for plotting
    errors, counts = zip(*top_type_errors)

    # Formatting labels
    formatted_errors = [format_label(error) for error in errors]
    formatted_errors[3], formatted_errors[4] = formatted_errors[4], formatted_errors[3] # reverse alphabetical order

    # Creating a bar chart
    plt.bar(formatted_errors, counts)
    plt.xlabel('Figure 4c: How developers use type checker hints.')
    plt.ylabel('Count')
    #plt.title(f'Top {top_n} Type Errors')
    plt.xticks(rotation=90)
    plt.ylim(0, 60)  # Setting the y-axis limit to 60
    plt.tight_layout()

    # Save the plot as a PDF file
    plt.savefig(output_file)
    plt.close()

    print(f"Plot saved as {output_file}")

# Path to the folder containing JSON files
folder_path = '.'

# Read JSON data from files
json_data = read_json_files(folder_path)

# Plot the top 5 type errors and save as
plot_top_type_errors(json_data)
