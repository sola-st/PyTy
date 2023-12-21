#! /usr/bin/env python

# from collections import Counter
import json
import os
import subprocess
import traceback

from utils import get_project_names

warning_types = [ 
    'Unbound name [10]',
    'Inconsistent override [15]',
    'Incompatible variable type ',
    'Incompatible return type ',
    'Incompatible parameter type ',
    'Invalid type [31]',
    'Inconsistent override [14]',
    'Incompatible attribute type ',
    'Unsupported operand [58]',
    'Call error [29]',
]

def git_checkout_latest(directory):
    """
    Checks out the latest commit in the git repository.
    """
    os.system("cd " + directory + " && git checkout -f $(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@') && git pull")

def git_get_current_commit(directory):
    """
    Returns the current commit hash.
    """
    return subprocess.check_output(["cd " + directory + " && git rev-parse HEAD"], shell=True).decode('utf-8').strip()

def run_pyre(cwd='~/dd-py3/pyre_input/'):
    try:
        subprocess.run("watchman watch .".split(" "), cwd=cwd)
        cmd = "pyre incremental"
        data = subprocess.check_output(cmd, cwd=cwd, shell=True, universal_newlines=True, stderr=subprocess.STDOUT)
        status = 0
    except subprocess.CalledProcessError as ex:
        data = ex.output
        status = ex.returncode
    if data[-1:] == '\n':
        data = data[:-1]
    return status, data

def get_lines_from_file_by_numbers(file_name, numbers):
    """
    Returns the lines from a file given by the numbers.
    """
    with open(file_name, 'r') as f:
        lines = f.readlines()
    numbers = [i for i in numbers if i-1 < len(lines) and i-1 > 0]
    return ''.join([lines[i-1] for i in numbers])

# Save the following variables as fields in a dictionary
# project_name, commit_hash, full_file_path, file_name, line_num, w_line, w_type, msg, source_code
def get_warning_info(project_name, commit_hash, full_file_path, file_name, line_num, w_line, w_type, msg, source_code):
    warning_info = {}
    warning_info['project'] = project_name
    warning_info['commit_hash'] = commit_hash
    warning_info['full_file_path'] = full_file_path
    warning_info['file_name'] = file_name
    warning_info['line_num'] = int(line_num)
    warning_info['w_line'] = w_line
    warning_info['type'] = w_type
    warning_info['msg'] = msg
    warning_info['source_code'] = source_code
    warning_info['source_code_len'] = len(source_code)
    return warning_info

# Save list of dictionary as json file
def save_json(data, file_name):
    with open(file_name, 'w') as f:
        f.write(json.dumps(data, indent=4))

project_set = get_project_names('./Input/')
for project_dir_name, project_name in project_set.items():
    project_dir = '../TypeAnnotation_Study/GitHub/'+project_dir_name
    project_warnings = []
    output_json_name = './eval_output/warnings/'+project_dir_name+'.json'
    # gitCheckoutLatest(project_dir)
    try:
        if not os.path.isfile(output_json_name):
            (status, pyre_res) = run_pyre(project_dir)
            # print(pyre_res)
            relevant_warnings = [line for line in pyre_res.split('\n') if any(t in line for t in warning_types)]
            print(relevant_warnings)
            for w in relevant_warnings:
                metadata, full_msg = w.split(' ',1)
                file_name, line_num, _ = metadata.split(':')
                full_file_path = project_dir+'/'+file_name
                w_type, msg = full_msg.split(':',1)
                commit_hash = git_get_current_commit(project_dir)
                # get 5 lines around the warning line
                line_numbers_to_get = [*range(int(line_num) - 2, int(line_num) + 3, 1)]
                w_line = get_lines_from_file_by_numbers(full_file_path, line_num)
                source_code = get_lines_from_file_by_numbers(full_file_path, line_numbers_to_get)
                # save the following variables as json
                project_warnings.append(get_warning_info(
                    project_name, commit_hash, full_file_path, file_name, line_num, w_line, w_type, msg, source_code))
            save_json(project_warnings, output_json_name)            
    except Exception as e:
        print('exception', e)
        print(traceback.format_exc())
    finally:
        subprocess.run("watchman watch-del .".split(" "), cwd=project_dir)
        subprocess.run("pyre stop".split(" "), cwd=project_dir)
    # break