from collections import defaultdict
from datetime import datetime
import multiprocessing
import subprocess
import pyreDD
import os
import json
from pathlib import Path
import traceback
import logging
from os.path import exists
from pygit2 import Repository

dir = r'~/TypeAnnotation_Study/Resources/Output_type_fix_commits_final/'

# TODO: filter by # of hunk is better
# max_w_in_file = 10 

# TODO: first step: only consider warning types with >=1% data points
warning_types = [
  "Incompatible parameter type [6]",
  "Incompatible variable type [9]",
  "Incompatible return type [7]",
  "Inconsistent override [15]",
  "Unbound name [10]",
  "Incompatible attribute type [8]",
  "Unsupported operand [58]",
  "Inconsistent override [14]",
  "Invalid type [31]",
  "Call error [29]",
]

def run_dd_on_dataset():
  # Separate by repo, otherwise the checking out commits will overwrite each other
  repo_wfile_dict = defaultdict(list)

  files = os.listdir(dir)
  for fn in files:
    try:
      if fn.startswith('compare_warning_') and fn.endswith('.json'):          
        with open(dir+fn) as f:
          data = json.load(f) 
          for d in data: 
            repo_wfile_dict[d['project']].append(fn)
    except Exception as e:
      logging.info(traceback.format_exc())
      logging.error(f"Cannot parse json, skip file {fn}")

  for i in repo_wfile_dict.items():
      run_dd(i)

def run_dd(p_fn_pair):
  target_p = 'aws/aws-sam-cli'
  target_commit = 'a6dc9bceb74008e5dac046d586438a63611e9292'
  target_warning = 'Call error [29]: `typing.Union[typing.Type[typing.Union[Parameter, Resource]], typing.Type[DictSectionItem]]` is not a function.'
  p, warning_fn_list = p_fn_pair
  if p != target_p:
    return
  for fn in warning_fn_list:
    try:
      if fn.startswith('compare_warning_') and fn.endswith('.json'):          
        with open(dir+fn) as f:
          data = json.load(f) 
          res = []
          for d in data: 
            p = d['project']
            p_path = p.replace('/', '-')
            commit = d['b_commit']
            if len(d['parent_warnings']) > 0:
              repo_dir = "~/TypeAnnotation_Study/GitHub/" + p_path
              dd_res_fn = '~/dd-py3/Output/'+"dd_out_"+p_path+"_"+commit[:7]+'.json'
              for w_in_file in d['parent_warnings']:
                for w in w_in_file:
                  if (
                    target_commit != commit
                    or 
                    target_warning not in w
                  ):
                    continue
                  if any(w_type in w for w_type in warning_types):
                    try:
                      # # Skip if dd already done on this warning                      
                      # if exists(dd_res_fn):
                      #   with open(dd_res_fn) as dd_f:
                      #     dd_data = json.load(dd_f) 
                      #     if any(w == o['full_warning_msg'] for o in dd_data):
                      #       logging.info(f"Skip: already done dd on warning: {fn} {w}")
                      #       continue
                      filename = w.split(':')[0]
                      buggy_filepath = fixed_filepath = repo_dir+'/'+filename
                      subprocess.run(f"git checkout -f {commit}".split(" "), cwd=repo_dir)
                      if exists(fixed_filepath):
                        after = Path(fixed_filepath).read_text()
                      else: # try to find the new filepath, assuming it's being renamed
                        repo = Repository(repo_dir)
                        diff = repo.diff(commit+'^', commit)
                        diff.find_similar()
                        for patch in diff:
                          if patch.delta.old_file.path == filename:
                            fixed_filepath = repo_dir+'/'+patch.delta.new_file.path
                            after = Path(fixed_filepath).read_text()
                            break
                        if not after:
                          raise Exception('Failed to find the buggy file after commit.')
                      subprocess.run(f"git checkout -f {commit}^".split(" "), cwd=repo_dir)
                      before = Path(buggy_filepath).read_text()
                      # must have watchman watching for pyre incremental to work
                      subprocess.run("watchman watch .".split(" "), cwd=repo_dir)
                      new_w_introduced = set()
                      for new_w_in_file in d['warnings']:                
                          for new_w in new_w_in_file:
                            if new_w.startswith(filename):
                              new_w_introduced.add(new_w.split(' ',1)[1])
                      res.append(pyreDD.dd(w, before, after, repo_dir, buggy_filepath, fixed_filepath, p, filename, commit, new_w_introduced))
                      logging.info(f"Done: dd on warning: {fn} {w}")
                    except Exception as e:
                      logging.info(traceback.format_exc())
                      logging.error(f"Cannot dd on warning: {fn} {w}")
                      subprocess.run("pyre stop".split(" "), cwd=repo_dir)
                      subprocess.run("watchman watch-del .".split(" "), cwd=repo_dir)
              if res:
                # write_results("dd_out_"+p_path+"_"+commit[:7], res)
                print(res)
                # Teardown pyre and watchman
                subprocess.run("pyre stop".split(" "), cwd=repo_dir)
                subprocess.run("watchman watch-del .".split(" "), cwd=repo_dir)

    except Exception as e:
      logging.info(traceback.format_exc())
      logging.error(f"Cannot parse json, skip file {fn}")
      subprocess.run("pyre stop".split(" "), cwd=repo_dir)
      subprocess.run("watchman watch-del .".split(" "), cwd=repo_dir)

# def write_results(name, results):
#   with open('~/dd-py3/Output/'+name+".json", "w") as fp:
#     fp.write(json.dumps(results, indent=2))

if __name__ == '__main__': 
  now = datetime.now()
  logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s', 
    level=logging.INFO, 
    datefmt='%Y-%m-%d %H:%M:%S', 
    filename='./dd_debugger.log')
  print("start time: ", now.strftime("%H:%M:%S"))
  logging.info("start time: {}".format(now.strftime("%H:%M:%S")))
  run_dd_on_dataset()
  now = datetime.now()
  print("end time: ", now.strftime("%H:%M:%S"))
  logging.info("end time: {}".format(now.strftime("%H:%M:%S")))