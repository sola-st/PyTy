import json
import os
import subprocess

from utils import get_project_names

def get_git_repo_stars(project_dir):
    """
    Returns the number of stars of a git repo.
    """
    cmd = 'cd '+project_dir+' && git rev-list --count HEAD'
    ex = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ex.stdout.decode('utf-8').strip()

def get_git_repo_latest_commit_time_after_july_31_2022(project_dir):
    """
    Returns the latest commit time of a git repo, after 2022-07-31.
    Assume these repos are committed daily, since the repos are pulled on 2022-08-01.
    """
    cmd = 'cd '+project_dir+' && git log --after="2022-07-31" --format=%ct'
    ex = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ex.stdout.decode('utf-8').strip()

project_set = get_project_names('./Input/')
count = 0
for project_dir_name, project_name in project_set.items():
    project_dir = '../TypeAnnotation_Study/GitHub/'+project_dir_name
    timestamp = get_git_repo_latest_commit_time_after_july_31_2022(project_dir)
    # print(project_name)
    if timestamp == '':
        # print('No commit after 2022-07-31')
        pass
    else:
        # print(timestamp)
        count += 1
        print('./eval_output/warnings/'+project_dir_name+'.json')
# print(count)