import json
import os
import time
import random

def random_select():
  directory = r'Output_fixed_TFix/'
  output_list = os.listdir(directory)
  n = 100
  random.shuffle(output_list)
  for data_file in output_list:
      with open(directory+data_file) as f:
        try:
          data = json.load(f) 
          for d in data: 
            try:
              if (
                d.get('fit_TFix') and 
                not d.get('delete_only_patch') and 
                not any(h['has_suppression'] for h in d['min_patch'])
              ):              
                print(directory+data_file)
                print(d['full_warning_msg'])
                print('https://github.com/'+d['project']+'/commit/'+d['commit'])
                for h in d["min_patch"]:
                  print(h['diff_format'])
                print('----------------------------------------------')
                n -= 1
                if n <= 0:
                  return
                break # go to another file for the next patch
            except Exception:
              pass
        except Exception:
          print(f"cannot parse json, skip file {f}")

if __name__ == '__main__': 
  random_select()
  start = time.asctime()
  print('Time: ' + start)
