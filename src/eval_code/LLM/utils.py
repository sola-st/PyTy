import json
import subprocess

# Read the JSON file
with open('./Input/test_data_baseline.json') as json_file:
    data = json.load(json_file)

# Iterate over the JSON objects
for obj in data:
    # Retrieve the repo field
    repo = obj['repo']
    print(f'Cloning {repo}...')

    # Clone the GitHub repository
    subprocess.run(['git', 'clone', 'https://github.com/'+repo+'.git', f'./github/{repo.replace("/", "_")}'])

    # Alternatively, you can use the gitpython library for more flexibility
    # from git import Repo
    # Repo.clone_from(repo, './github')
