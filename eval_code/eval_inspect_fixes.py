"""
Selects a subset of our test dataset for manual inspection (to check how many type errors manifested via runtime errors).
"""

from os.path import join
import json
import random

random.seed(42)   # fix random seed for reproducibility

with open(join("output", "test_data_baseline.json")) as f:
    test_data = json.load(f)
    print(f"Number of entries: {len(test_data)}")

sample = random.sample(test_data, 30)
inspection_template = []
for entry in sample:
    commit_url = f"http://github.com/{entry['repo']}/commit/{entry['target_changeid']}"
    inspection_template.append({
        "commit_url": commit_url,
        "comment": ""
    })

with open(join("output", "manual_commit_inspection_template.json"), "w") as f:
    json.dump(inspection_template, f, indent=2)

print(f"Number of entries in inspection template: {len(inspection_template)}")