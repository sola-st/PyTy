import subprocess
import datetime
import logging
import json
from pathlib import Path
from git import Repo

def check_error_removal():
    # Read the JSON file
    with open('./input/test_data_baseline.json') as json_file:
        full_input = json.load(json_file)

    with open('./output/text-davinci-003_fixes.json') as json_file:
        prediction_input = json.load(json_file)

    # Iterate over the JSON objects
    for index, obj in enumerate(full_input):
        # Retrieve the repo field
        repo = obj['repo']
        repo_dir = f'./github/{repo.replace("/", "_")}'
        # Retrieve the target filename
        target_filename = obj['source_filename']
        # Retrieve the target change ID
        target_changeid = obj['target_changeid']

        # Run pyre to get the warnings before fixing
        subprocess.run("watchman watch .".split(" "), cwd=repo_dir)
        (status, pyre_res_before) = run_pyre(repo_dir)
        old_w_set = set()
        for w in pyre_res_before.split('\n'):              
            if w.startswith(target_filename):
                old_w_set.add(w)
                
        break

def run_pyre(cwd='~/dd-py3/pyre_input/'):
    try:
        cmd = "pyre incremental"
        data = subprocess.check_output(cmd, cwd=cwd, shell=True, universal_newlines=True, stderr=subprocess.STDOUT)
        status = 0
    except subprocess.CalledProcessError as ex:
        data = ex.output
        status = ex.returncode
    if data[-1:] == '\n':
        data = data[:-1]
    return status, data

if __name__ == '__main__': 
  now = datetime.now()
  logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s', 
    level=logging.INFO, 
    datefmt='%Y-%m-%d %H:%M:%S', 
    filename='./check_error.log')
  print("start time: ", now.strftime("%H:%M:%S"))
  logging.info("start time: {}".format(now.strftime("%H:%M:%S")))
  check_error_removal()
  now = datetime.now()
  print("end time: ", now.strftime("%H:%M:%S"))
  logging.info("end time: {}".format(now.strftime("%H:%M:%S")))