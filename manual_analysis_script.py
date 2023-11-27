# Output top-k predictions in a format that is easy to manually check

from collections import defaultdict
from datetime import datetime
import re
import subprocess
import json
from pathlib import Path
import traceback
import logging
from os.path import exists

eval_data_list = [
  'output/error_removal_analysis_baseline.json',
  # 'output/error_removal_analysis_t5large.json',
  # 'output/error_removal_analysis_noTFix_100ep.json',
]

count = 0

# Check top-1
for ed in eval_data_list:
  with open(ed) as f:
    print(ed+'\n')
    err_removal = json.load(f) 
    for d in err_removal:      
      try:
        # if d['top-1_removal']: -> manual_check_top1.txt
        # if d['top-3_removal'] and not d['top-1_removal']: -> manual_check_top3.txt
        # if d['top-3_removal'] and d['top-1_removal'] and not d.get('manual_eval_top1'): -> manual_check_top3_failTop1.txt
        if d['top-5_removal'] and not d.get('manual_eval_top1') and not d.get('manual_eval_top3'): # -> manual_check_top5.txt
          print('https://www.github.com/'+d['repo']+'/commit/'+d['commit'])
          print(d['filename']+':'+str(d['warning_line'])+' '+d['warning_type']+':'+d['warning_message'])
          print('Source Code:')
          print(d['source_code'])
          # if d['pred_top-1']['warning_removed']:
          #   print('Prediction 1:')
          #   print(d['pred_top-1']['pred_parsed'])
          # if d['pred_top-2']['warning_removed']:
          #   print('Prediction 2:')
          #   print(d['pred_top-2']['pred_parsed'])
          # if d['pred_top-3']['warning_removed']:
          #   print('Prediction 3:')
          #   print(d['pred_top-3']['pred_parsed'])
          if d['pred_top-4']['warning_removed']:
            print('Prediction 4:')
            print(d['pred_top-4']['pred_parsed'])
          if d['pred_top-5']['warning_removed']:
            print('Prediction 5:')
            print(d['pred_top-5']['pred_parsed'])
          print('Target Code:')
          print(d['target_code'])
          print('----------------------------------------------')
          count += 1
      except:
        pass

print('Checked', count)

# Add repo name to json
# repo_name_list = []
# with open('test_data_baseline.json') as f:
#     td = json.load(f) 
#     for d in td:
#         repo_name_list.append(d['repo'])

# for ed in eval_data_list:
#   with open(ed) as f:
#     print(ed)
#     err_removal = json.load(f) 
#     for d in err_removal:
#       for name in repo_name_list:
#         if name.replace('/','-') in d['repo_dir']:
#           d['repo'] = name
#           count += 1
#           break
#     with open(ed, "w") as fp:
#       fp.write(json.dumps(err_removal, indent=2))
