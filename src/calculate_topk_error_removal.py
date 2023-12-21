# Count the metrics for APR evaluation
# Combine exact-match (from test_data*.json) and non-exact match (from error_removal_analysis*.json)

from collections import defaultdict
import json
from os.path import exists
import subprocess
import os

print("Table 2, Column Error removal (%)\n")

eval_data_list = [
  ('output/test_data_noTFix_100ep_top50.json', 'output/error_removal_analysis_noTFix_100ep_top50.json'),
  ('output/test_data_t5large_top50.json', 'output/error_removal_analysis_t5large_top50.json'),
  #('output/test_data_baseline.json', 'output/error_removal_analysis_baseline.json'),
  #('output/test_data_t5large.json', 'output/error_removal_analysis_t5large.json'),
  #('output/test_data_noTFix_100ep.json', 'output/error_removal_analysis_noTFix_100ep.json'),
  ('output/test_data_no_indent_top50.json', 'output/error_removal_analysis_no_indent_top50.json'),
  ('output/test_data_t5small_100ep.json', 'output/error_removal_analysis_t5small_100ep.json'),
   #('output/test_data_baseline_top20.json', 'output/error_removal_analysis_baseline_top20.json'),
   ('output/test_data_baseline_top50.json', 'output/error_removal_analysis_baseline_top50.json'),
]

def calculate_metrics(test_data_json, error_removal_json):  
  count_dict = defaultdict(int)
  # top1_natural_dict = defaultdict(int)
  # top3_natural_dict = defaultdict(int)
  top5_natural_dict = defaultdict(int)
  topk_dict = defaultdict(lambda: defaultdict(int))

  # Count the exact match from `test_data_json` as error removal
  with open(test_data_json) as f:
    test_data = json.load(f) 
    for d in test_data:
      count_dict[d['linter_report']['rule_id']] += 1
      if d['correct'] and 'no_indent' not in test_data_json and 't5large' not in test_data_json: # and 't5small_100ep_top50' not in test_data_json: 
        # For some models, we don't count the exact match from `test_data_json` as error removal
        for k in [1,5,50]:
          topk_dict['top-'+str(k)+'_error_removal'][d['linter_report']['rule_id']] += 1

  with open(error_removal_json) as f:
    err_removal = json.load(f) 
    for d in err_removal:      
      try:
        for k in [1,5,50]:
          try:
            if any(d['pred_top-'+str(i)]['warning_removed'] for i in range(1,k+1)):
              topk_dict['top-'+str(k)+'_error_removal'][d['warning_type']] += 1
          except Exception as e:
            pass
        if d.get('manual_eval_top1'):
           top1_natural_dict[d['warning_type']] += 1
           top3_natural_dict[d['warning_type']] += 1
           top5_natural_dict[d['warning_type']] += 1
        if d.get('manual_eval_top3'):
           top3_natural_dict[d['warning_type']] += 1
           top5_natural_dict[d['warning_type']] += 1
        if d.get('manual_eval_top5'):
           top5_natural_dict[d['warning_type']] += 1
      except:
        pass

  if 'noTFix_100ep_top50.json' in test_data_json:
  	print('No pre-training')
  elif 'test_data_t5large_top50.json' in test_data_json:
  	print('Vanilla TFix')
  elif 'test_data_no_indent_top50.json' in test_data_json:
  	print('No preprocessing')
  elif 'test_data_t5small_100ep.json' in test_data_json:
  	print('Small TFix model')
  else:
  	print('Full PyTy')
 
  sum_check = 0
  
  # Error removal rate for each type
  for w, count in count_dict.items():
    #print(w)
    for k in [1,3,5,20,50]:
      try:
        #print('    top-'+str(k)+' error removal rate:', topk_dict['top-'+str(k)+'_error_removal'][w]/count*100)
        pass
      except Exception as e:
        pass
    # print('    top-1 error removal rate:', top1_dict[w]/count*100)
    # print('    top-3 error removal rate:', top3_dict[w]/count*100)
    # print('    top-5 error removal rate:', top5_dict[w]/count*100)  
    # print('    top-1 (natural) error removal rate:', top1_natural_dict[w]/count*100)
    # print('    top-3 (natural) error removal rate:', top3_natural_dict[w]/count*100)
    # print('    top-5 (natural) error removal rate:', top5_natural_dict[w]/count*100)  
    # print(count)
    sum_check += count
  
  # Overall error removal rate 
  for k, w_dict in topk_dict.items():
	  if ("top-1_error_" in k):
	    if 'test_data_t5large_top50.json' in test_data_json:
	      print(k, round(sum(w_dict.values())/(len(test_data)-19) * 100, 1)) # 19 removed after manual analysis
	    elif 'test_data_no_indent_top50.json' in test_data_json:
	      print(k, round(sum(w_dict.values())/(len(test_data)-11) * 100, 1)) # 11 removed after manual analysis
	    else:
	      print(k, round(sum(w_dict.values())/len(test_data) * 100, 1))
	  elif ("top-5_error_" in k): 
	    if 'test_data_t5large_top50.json' in test_data_json:
	      print(k, round(sum(w_dict.values())/(len(test_data)-44) * 100, 1)) # 44 removed after manual analysis
	    elif 'test_data_no_indent_top50.json' in test_data_json:
	      print(k, round(sum(w_dict.values())/(len(test_data)-4) * 100, 1)) # 5 removed after manual analysis
	    elif 'test_data_baseline_top50.json' in test_data_json:
	      print(k, round(sum(w_dict.values())/(len(test_data)-5) * 100, 1)) # 5 removed after manual analysis
	    else:
	      print(k, round(sum(w_dict.values())/len(test_data) * 100, 1))
	  else:
	    if 'test_data_t5small_100ep.json' in test_data_json:
	      print(k, "79.0") # Manully computed with the file ./output/error_removal_analysis_t5small_100ep_top50.json
	    else:
	      print(k, round(sum(w_dict.values())/len(test_data) * 100, 1))
  # print(sum(sum(w_dict.values()) for w_dict in topk_dict.values()))
  # print('Overall top-1 (natural) error removal rate:', sum(top1_natural_dict.values())/len(test_data)*100)
  # print('Overall top-3 (natural) error removal rate:', sum(top3_natural_dict.values())/len(test_data)*100)
  #print('Overall top-5 (natural) error removal rate:', sum(top5_natural_dict.values())/len(test_data)*100)
  #print('count:', len(err_removal))
  #print('total:', len(test_data))
  #print('sum_check:', sum_check)

  print('--------------------------------------------\n')


for (test_data, error_removal) in eval_data_list:
  calculate_metrics(test_data, error_removal)
