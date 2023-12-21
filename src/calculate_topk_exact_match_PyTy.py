# Count the metrics for APR evaluation
# Combine exact-match (from test_data*.json) and non-exact match (from error_removal_analysis*.json)

from collections import defaultdict
from datetime import datetime
import re
import subprocess
import json
from pathlib import Path
import traceback
import logging
import re
from os.path import exists

pattern = r"\[\d+\]"

eval_data_list = [
  # 'output/test_data_baseline.json',
  # 
  #'output/test_data_noTFix_100ep_top50.json',
  #'output/test_data_t5large_top50.json',
  #'output/test_data_no_indent_top50.json',
  # 'output/test_data_no_indent.json',
  # 'output/test_data_t5small_100ep_top5.json',
  # # 'output/test_data_baseline_top20.json',
   # 'output/test_data_t5small_100ep_top50.json',
  'output/test_data_baseline_top50.json',
  # 'output/test_data_noTFix_100ep_top50.json',
  # 'output/test_data_t5large_top50.json',
  # 

]

print("Table 1, Column Exact Match\n")

def calculate_metrics(test_data_json):  
  count_dict = defaultdict(int)
  topk_dict = defaultdict(lambda: defaultdict(int))
    
  with open(test_data_json) as f:
    test_data = json.load(f) 
    for d in test_data:
      count_dict[d['linter_report']['rule_id']] += 1
      topK_match = d["top_five_exact_match"]
      for k in [1,3,5,20,50]:
        try:
          if any(topK_match[str(i)] for i in range(k)):
            topk_dict['top-'+str(k)+'_exact_match'][d['linter_report']['rule_id']] += 1
        except Exception as e:
          pass
          #print('Passing Exception', e)
          #print('k', k)
    
    #print(test_data_json)
    sum_check = 0
    #print(topk_dict)
    for w, count in count_dict.items():
        #print(w)
        for k in [50]:
          try:
          	
          	print(re.sub(pattern, "", w) + ':' ,'top-'+str(k)+' exact match:', round(topk_dict['top-'+str(k)+'_exact_match'][w]/count*100, 1))
          except Exception as e:
            pass
        sum_check += count

    for k, w_dict in topk_dict.items():
    	if  ("top-50_exact_" in k):
    		#print("\n")
      		print(k, sum(w_dict.values()), round(sum(w_dict.values())/len(test_data) * 100, 1))
    
#print('total:', len(test_data))
    #print('sum_check:', sum_check)  
  print('--------------------------------------------')


for (test_data) in eval_data_list:
  calculate_metrics(test_data)
