from collections import defaultdict
from datetime import datetime
import multiprocessing
import re
import subprocess
import os
import json
from pathlib import Path
import sys
import traceback
from os.path import exists
import tokenize
import io

"""
Compared to check_error_all.py, this script:
(1) checkout the commit stated in the JSON (not commit+"^")
(2) also output a result JSON per project, instead of a single result JSON with all projects
(3) don't count same_as_source
(4) no logging 
(5): runs in parellel
"""

# output/test_data_*.json
test_data = r't5base_final_test_eval_active_daily_project/test_data.json'

def error_check_helper(repo_warnings_pair):
  repo, warnings_list = repo_warnings_pair
  for d in warnings_list:
      p = d['repo']
      p_path = p.replace('/', '-')
      commit = d['target_changeid']
      repo_dir = "../TypeAnnotation_Study/GitHub/" + p_path
      res = {}
      # Check if errors are removed in all predictions
      warning_removed_top_five = []
      src_code = d['source_code'].replace('<IND>','').replace('<DED>','').lstrip('\n').rstrip()
      filename = d['source_filename']
      buggy_filepath = repo_dir+'/'+filename
      res['repo'] = p
      res['repo_dir'] = repo_dir
      res['commit'] = commit
      res['filename'] = filename
      res['source_code'] = src_code
      res['target_code'] = d['target_code']
      res['warning_type'] = d['linter_report']['rule_id']
      res['warning_message'] = d['linter_report']['message']
      res['warning_line'] = d['linter_report']['line_begin']        
      for k, pred in d['top_five'].items():
        try:
          if d['source_code'].replace(' ','') == pred.replace(' ',''):
            same_as_src_count += 1
          subprocess.run(f"git checkout -f {commit}".split(" "), cwd=repo_dir)
          before = Path(buggy_filepath).read_text()

          # Run pyre to get the warnings before fixing
          subprocess.run("watchman watch .".split(" "), cwd=repo_dir)
          (status, pyre_res_before) = run_pyre(repo_dir)
          old_w_set = set()
          for w in pyre_res_before.split('\n'):              
            if w.startswith(filename):
              old_w_set.add(w)
          
          # Find the indent level of the first line of the hunk
          # Use while loop to find the actual hunk, in case there are multiple src_code matches
          line_num = float('-inf')
          search_start = 0
          while not (line_num <= d['linter_report']['line_begin'] <= line_num + src_code.count('\n')):
            char_loc = before.index(src_code, search_start)
            line_idx = len([c for c in before[:char_loc] if c == '\n'])
            first_line = before.splitlines()[line_idx]
            indent = len(first_line) - len(first_line.lstrip())
            line_num = line_idx + 1
            search_start = char_loc+1
            # if indent % 4 != 0:
              # print(indent)
          
          # Calculate indent and output the predictions (assume indent is always 4 whitespaces)
          output = ''
          pred_lines = pred.lstrip('\n').rstrip().split('\n')
          for i in range(len(pred_lines)):
            # Process indentation tokens only if it is not the first line and previous line is not a comment
            # We don't need to handle first line,
            # because we will use the indent level of the first line directly (the `indent` variable)
            if i != 0 and not pred_lines[i-1].startswith('#'):
              indent += pred_lines[i].count('<IND>')*4
              indent -= pred_lines[i].count('<DED>')*4
            output += indent*' '+pred_lines[i].replace('<IND>','').replace('<DED>','').strip()+'\n'
          # print((src_code))
          # print(output)

          with open(buggy_filepath, "w") as fp:
            fp.write(before.replace(src_code, output))
          
          # Run pyre to check if error is removed
          # must have watchman watching for pyre incremental to work
          (status, pyre_res) = run_pyre(repo_dir)
          new_w_set = set()
          warning_removed = True
          fail_reason = 'N/A'
          
          # Check the error should not appear in pred_lines (via getting '\n'-1 in predictions)
          num_lines = output.count('\n')
          for w in pyre_res.split('\n'):              
            if w.startswith(filename):
              if 'Parsing failure' in w:
                warning_removed = False
                fail_reason = 'Parsing failure'
              w_line_num = int(re.search(r":\d+:", w).group().strip(':'))
              # lines within the diff: don't record line number as we don't know how it changes
              if line_num <= w_line_num <= line_num+num_lines:
                new_w_set.add(w.split(' ',1)[1])
              else:
                new_w_set.add(w)
              for l in range(line_num, line_num+num_lines+1):
                if w.startswith(filename+':'+str(l)) and w.endswith(d['linter_report']['message']):
                  fail_reason = 'Error Still Exists'
                  warning_removed = False

          # Check no other new error appears (via calculating new line no. of the warnings in old_w)
          old_w_set_updated = set()
          line_diff = num_lines - src_code.count('\n')
          for w in old_w_set:
            w_line_num = int(re.search(r":\d+:", w).group().strip(':'))
            # lines after the diff are adjusted by line_diff
            if w_line_num > line_num+num_lines:
              w_line_num += line_diff
              w_updated = re.sub(r":\d+:", ':'+str(w_line_num)+':', w)
              old_w_set_updated.add(w_updated)
            # lines before the diff are not affected
            elif w_line_num < line_num:
              old_w_set_updated.add(w)
            # lines within the diff: don't record line number as we don't know how it changes
            else:
              old_w_set_updated.add(w.split(' ',1)[1])
          if len(new_w_set - old_w_set_updated) > 0:
            warning_removed = False
            fail_reason = 'New Error(s) Appear'
          k_str = str(int(k)+1)
          res['pred_top-'+k_str] = {}
          res['pred_top-'+k_str]['pred'] = pred
          res['pred_top-'+k_str]['pred_parsed'] = output
          res['pred_top-'+k_str]['warning_removed'] = warning_removed
          res['pred_top-'+k_str]['fail_reason'] = fail_reason
          warning_removed_top_five.append(warning_removed)  
        except Exception as e:
          pass

      try:
        res['top-1_removal'] = res['pred_top-1']['warning_removed']
        res['top-3_removal'] = any(res['pred_top-'+str(i)]['warning_removed'] for i in range(1,4))
        res['top-5_removal'] = any(res['pred_top-'+str(i)]['warning_removed'] for i in range(1,6))
        with open('eval_output/error_removal/'+p_path+'.json', "w") as fp:
          fp.write(json.dumps(res, indent=2))
      except Exception as e:
        res['exception'] = str(e)

      subprocess.run("watchman watch-del .".split(" "), cwd=repo_dir)
      subprocess.run("pyre stop".split(" "), cwd=repo_dir)
      return res

def check_error_removal():
  with open(test_data) as f:
    data = json.load(f) 
    res_list = []
    group_by_repo = defaultdict(list)
    for d in data: 
      # filter if it is a incompatible var type + assign to None type
      # TODO: might filter out potentially interesting warnings?
      # num of data with filter = 825, without = 1470
      if (
        d["linter_report"]["rule_id"] == "Incompatible variable type [9]"
        and 'is used as type `None`.' in d["linter_report"]["message"]
      ):
        continue
      group_by_repo[d['repo']].append(d) 
    # sum values in group_by_repo to get the total number of elements in each repo
    total_num_data = {k: len(v) for k, v in group_by_repo.items()}
    print('total_num_data', sum(total_num_data.values()))

    # Group by repo for multiprocessing so that each repo is handled by a single process
    with multiprocessing.Pool(4) as p:
      for res in p.imap_unordered(error_check_helper, group_by_repo.items()):
          res_list.append(res) 

    with open('eval_output/error_removalaa/total.json', "w") as fp:
      fp.write(json.dumps(res_list, indent=2))

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
  print("start time: ", now.strftime("%H:%M:%S"))
  check_error_removal()
  now = datetime.now()
  print("end time: ", now.strftime("%H:%M:%S"))
