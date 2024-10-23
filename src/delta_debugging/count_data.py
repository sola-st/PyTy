from collections import defaultdict
from itertools import groupby
import json
import math
import os
import time
import traceback

# -------- Count --------
directory = r'Output_fixed_TFix/'
count = 0
min_patch_found = 0
useful_patch = 0
delete_patch = 0
suppress_patch = 0
small_useful_patch = 0
single_hunk = 0
useful_single_hunk = 0
small_useful_single_hunk = 0
fit_TFix = 0
no_256 = 0
pyre_error_dict = defaultdict(lambda: 0)
pyre_error_dict_filtered = defaultdict(lambda: 0)
min_hunk_dict = defaultdict(lambda: 0)
min_hunk_dict_filtered = defaultdict(lambda: 0)
min_hunk_size_dict = defaultdict(lambda: 0)
hunk_count_dict = defaultdict(lambda: 0)
hunk_count_dict_filtered = defaultdict(lambda: 0)
except_dict = defaultdict(lambda: 0)
commit_count = 0
for data_file in os.listdir(directory):
    with open(directory+data_file) as f:
      commit_count += 1
      try:
        data = json.load(f) 
        for d in data: 
          try:
            count += 1
            if d.get('dd_fail'):
              if 'No such file or directory' in d['exception']:
                except_dict['No such file or directory'] += 1
              else:
                except_dict[d['exception']] += 1
                # if 'PatchSet' in d['exception']:
                #   print(data_file, d)
                #   break
            if 'file_hunks_size' in d:
              hunk_count_dict[d['file_hunks_size']] += 1
            if d['min_patch_found']:
              min_patch_found += 1
              pyre_error_dict[d['rule_id']] += 1
              min_hunk_dict[len(d['min_patch'])] += 1
              for h in d['min_patch']:
                min_hunk_size_dict[(h["source_code_len"]+h["target_code_len"])/2] += 1
                # min_hunk_size_dict[h["target_code_len"]] += 1
            if d['min_patch_found'] and not d.get('delete_only_patch') and not any(h['has_suppression'] for h in d['min_patch']):
              useful_patch += 1
            if d['min_patch_found'] and d.get('delete_only_patch'):
              delete_patch += 1
            if d['min_patch_found'] and any(h['has_suppression'] for h in d['min_patch']):
              suppress_patch += 1
            if d['min_patch_found'] and not d.get('delete_only_patch') and not any(h['has_suppression'] for h in d['min_patch']) \
              and all(h['target_code_len'] <= 256 for h in d['min_patch']):
              small_useful_patch += 1
              min_hunk_dict_filtered[len(d['min_patch'])] += 1
              if 'file_hunks_size' in d:
                hunk_count_dict_filtered[d['file_hunks_size']] += 1
            if d.get('single_hunk'):
              single_hunk += 1
            if d.get('single_hunk') and not d.get('delete_only_patch') and not any(h['has_suppression'] for h in d['min_patch']):
              useful_single_hunk += 1
            if d.get('single_hunk') and not d.get('delete_only_patch') and not any(h['has_suppression'] for h in d['min_patch']) \
              and d['min_patch'][0]['target_code_len'] <= 256:
              small_useful_single_hunk += 1
            if d.get('fit_TFix') and not d.get('delete_only_patch') and not any(h['has_suppression'] for h in d['min_patch']):
              fit_TFix += 1
              pyre_error_dict_filtered[d['rule_id']] += 1
          except Exception as e:
            print(traceback.format_exc())
            pass
      except Exception:
        print(f"cannot parse json, skip file {f}")

print('Error-fixing commit count: ', commit_count)
print('Processed data point count: ', count)
print('min_patch_found count: ', min_patch_found)
print('delete_patch count: ', delete_patch)
print('suppress_patch count: ', suppress_patch)
print('Patch count after filtering remove-only and suppression: ', useful_patch)
print('Patch count (output <=256 char) after filtering remove-only and suppression: ', small_useful_patch)
print('single_hunk count: ', single_hunk)
print('single_hunk count after filtering remove-only and suppression: ', useful_single_hunk)
print('single_hunk count (output <=256 char) after filtering remove-only and suppression: ', small_useful_single_hunk)
print('fit_TFix (fix location == error location && (output <=256 char) after filtering remove-only and suppression): ', fit_TFix)

except_dict = dict(sorted(except_dict.items(), key=lambda item: item[1], reverse=True))
r = json.dumps(except_dict, indent=4)
print('Exceptions when dd failed: ', r)

pyre_error_dict = dict(sorted(pyre_error_dict.items(), key=lambda item: item[1], reverse=True))
r = json.dumps(pyre_error_dict, indent=4)
print('Error type distribution if min_patch_found: ', r)

pyre_error_dict_filtered = dict(sorted(pyre_error_dict_filtered.items(), key=lambda item: item[1], reverse=True))
r = json.dumps(pyre_error_dict_filtered, indent=4)
print('Error type distribution fit_TFix: ', r)

min_hunk_dict = dict(sorted(min_hunk_dict.items(), key=lambda item: item[0], reverse=False))
r = json.dumps(min_hunk_dict, indent=4)
print('Number of hunks in min_patch distribution if min_patch_found: ', r)

min_hunk_dict_filtered = dict(sorted(min_hunk_dict_filtered.items(), key=lambda item: item[0], reverse=False))
r = json.dumps(min_hunk_dict_filtered, indent=4)
print('Number of hunks in min_patch distribution (output <=256 char) after filtering remove-only and suppression: ', r)

key_fn, result = lambda x: math.floor(x[0]/16) + 1  if x[0] % 16 else math.floor(x[0] / 16), {}
for item, grp in groupby(sorted(hunk_count_dict_filtered.items(), key = key_fn), key_fn):
  result[((item - 1) * 16 + 1, item * 16)] = sum(count for _, count in grp)
print('Number of hunks in the file distribution (output <=256 char) after filtering remove-only and suppression): ')
for r in result.items():
  print(r)

for item, grp in groupby(sorted(hunk_count_dict.items(), key = key_fn), key_fn):
  result[((item - 1) * 16 + 1, item * 16)] = sum(count for _, count in grp)
print('Number of hunks in the file distribution: ')
for r in result.items():
  print(r)

# min_hunk_size_dict = dict(sorted(min_hunk_size_dict.items(), key=lambda item: item[0], reverse=False))
# r = json.dumps(min_hunk_size_dict, indent=4)
# print('Size of hunks in min_patch distribution if min_patch_found: ', r)

key_fn, result = lambda x: math.floor(x[0]/256) + 1  if x[0] % 256 else math.floor(x[0] / 256), {}
for item, grp in groupby(sorted(min_hunk_size_dict.items(), key = key_fn), key_fn):
  result[((item - 1) * 256 + 1, item * 256)] = sum(count for _, count in grp)
print('Size of hunks in min_patch distribution if min_patch_found: ')
for r in result.items():
  print(r)

print(sum(min_hunk_size_dict.values()))

start = time.asctime()
print('Time: ' + start)
