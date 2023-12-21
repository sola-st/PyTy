# To update the 'source_code' and 'target_code' field to the correct format, no need to run if using up-to-date pyreDD.py
import json
import sys
import os
import traceback

# -------- Count --------
directory = r'Output/'
for data_file in os.listdir(directory):
    with open(directory+data_file) as f:
      try:
        data = json.load(f) 
        for d in data: 
          try:
            if d.get('min_patch'):
              for hunk in d['min_patch']:
                old_lines = []
                new_lines = []
                for d in hunk['diff_format'].splitlines(True):
                  if d.startswith('-'): # old lines
                    old_lines.append(d[1:])
                  elif d.startswith('+'): # new lines
                    new_lines.append(d[1:])
                  elif d.startswith(' '):
                    old_lines.append(d[1:])
                    new_lines.append(d[1:])
                  old_lines_str = ''.join(old_lines)
                  new_lines_str = ''.join(new_lines)
                hunk['source_code'] = old_lines_str
                hunk['source_code_len'] = len(old_lines_str)
                hunk['target_code'] = new_lines_str
                hunk['target_code_len'] = len(new_lines_str)                
          except Exception as e:
            print(traceback.format_exc())
            pass
      except Exception:
        print(f"cannot parse json, skip file {f}")
    
    # Write the updated fields back to the file
    with open(directory+data_file, "w") as f:
      json.dump(data, f, indent=2)

print('Done')