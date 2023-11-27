from collections import defaultdict
from datetime import datetime
import multiprocessing
import re
import subprocess
import os
import json
from pathlib import Path
import traceback
import logging
from os.path import exists
import tokenize
import io

# output/test_data_*.json
test_data = r'output/test_data_baseline_top50.json'

def check_error_removal():
  with open(test_data) as f:
    data = json.load(f) 
    same_as_src_count = 0
    res_list = []
    for d in data: 
      p = d['repo']
      p_path = p.replace('/', '-')
      commit = d['target_changeid']
      repo_dir = "~/TypeAnnotation_Study/GitHub/" + p_path
      res = {}
      # Only check if errors are removed in non-exact match predictions
      if not d['correct']:
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
            subprocess.run(f"git checkout -f {commit}^".split(" "), cwd=repo_dir)
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
            logging.info(f"Check {d['linter_report']['message']} from line {line_num} to {line_num+num_lines} ")
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
            
            # Logging
            logging.info(f"Done: check if warning removed in top-{k_str}: {warning_removed}")
            logging.info(pred)
            logging.info(buggy_filepath)
            logging.info(d['linter_report']['message']+':'+str(d['linter_report']['line_begin']))

            logging.info(f"len(new_w_set - old_w_set_updated) > 0: {len(new_w_set - old_w_set_updated) > 0}")
            logging.info("old_w_set_updated:")
            logging.info('\n'.join(old_w_set_updated))
            logging.info("new_w_set - old_w_set_updated:")
            logging.info('\n'.join(new_w_set - old_w_set_updated))

            warning_removed_top_five.append(warning_removed)  
          except Exception as e:
            logging.error(traceback.format_exc())
            logging.error(f"Failed on prediction data (top-{k_str}): {d}")

        try:
          res['top-1_removal'] = res['pred_top-1']['warning_removed']
          res['top-3_removal'] = any(res['pred_top-'+str(i)]['warning_removed'] for i in range(1,4))
          res['top-5_removal'] = any(res['pred_top-'+str(i)]['warning_removed'] for i in range(1,6))
          res_list.append(res)
        except Exception as e:
          logging.error(traceback.format_exc())
          logging.error(f"Failed on prediction data: {d}")
          res['exception'] = str(e)
          res_list.append(res)

        logging.info(f"At least one in top-5 removed warnings: {any(warning_removed_top_five)}")
        logging.info('--------------------------------------------------')
        subprocess.run("watchman watch-del .".split(" "), cwd=repo_dir)
        subprocess.run("pyre stop".split(" "), cwd=repo_dir)
    print('same_as_src_count', same_as_src_count)
    with open('output/error_removal_analysis_t5small_100ep_top5.json', "w") as fp:
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

# ------------------------------------------
# Alternatives to replace source code with predictions:

# TODO: alternative 1: replace before.splitlines()[first_line:first_line+num_lines] with the [predictions] lines
# Use the first_line.replace(first_line.strip()) method to keep the indentations (assume indentations are correct)
# For now, ignore the ones wit different number of lines in patch
# if d['source_code'].strip().count('\n') != d['predictions'][0].strip().count('\n'):
#   print('newline miss:',d['source_code'])
# TODO: alternative 2: replace the src_lines with predictions as tokens, then untokenize
# break
# src_lines = src_code.splitlines()
# before_lines = before.splitlines()
# for i in range(len(before_lines)):
#   if before_lines[i] == src_lines[0]:
#     found = True
#     for sl in src_lines:
#       found = found & sl==before_lines[]
#     if found:
#       print('found', i)

# occurrence = d['linter_report']['line_begin']-1
# Finding nth occurrence of substring
# char_loc = -1
# for i in range(0, occurrence):
#     char_loc = before.find('\n', char_loc + 1)
# print(before[char_loc:before.find('\n', char_loc + 1)])
# print(before[char_loc:before.find('\n', char_loc + 1)])
# print('----------------------')
# print(src_code)

# id = before.count(src_code)
# if id != 1:
#   print(id)
#   print(d['source_code'])
  # lst += str(id)+', '
