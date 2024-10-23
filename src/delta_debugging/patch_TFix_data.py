from collections import defaultdict
import json
import os
import time
import traceback
from parse import parse

# -------- Count --------
directory = r'Output/'
fit_TFix_count = 0
fit_TFix_filtered_count = 0
err_count = 0
hunk_err_count = 0
for data_file in os.listdir(directory):
    with open(directory+data_file) as f:
      try:
        data = json.load(f) 
        for d in data: 
          try:
            if d['min_patch_found']:
              for min_hunk in d['min_patch']:
                # Check if warning line lies in line_window (via counting line no.)
                inside_window = False
                line_info = parse('@@ -{},{} +{},{} @@', min_hunk['diff_format'].splitlines()[0]) # first line is @@ ... @@
                startsrc = int(line_info[0])
                linessrc = int(line_info[1])
                if startsrc <= d['warning_line_no'] <= startsrc+linessrc-1:
                  inside_window = True
                
                if (
                  inside_window and
                  min_hunk['target_code_len'] <= 512 and
                  min_hunk['source_code_len'] <= 512 and
                  sum([1 for d in min_hunk['diff_format'].splitlines() if d.startswith('+') == True]) <= 3 and
                  sum([1 for d in min_hunk['diff_format'].splitlines() if d.startswith('-') == True]) <= 3 
                  # and len(min_hunk['diff_format'].splitlines()) <= 10
                ):                  
                  min_hunk['hunk_fit_TFix'] = True
                else:
                  min_hunk['hunk_fit_TFix'] = False
                  
              if len(d['min_patch']) == 1 and d['min_patch'][0]['hunk_fit_TFix'] \
                and not d.get('delete_only_patch') and not any(h['has_suppression'] for h in d['min_patch']):
                d['fit_TFix'] = True
                fit_TFix_count += 1
              else:
                d['fit_TFix'] = False
          except Exception as e:
            print(traceback.format_exc())
            pass
      except Exception:
        print(f"cannot parse json, skip file {f}")
        print(traceback.format_exc())

print('fit_TFix_count:', fit_TFix_count)

start = time.asctime()
print('Time: ' + start)