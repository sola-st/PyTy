# Count the metrics for APR evaluation
# Combine exact-match (from test_data*.json) and non-exact match (from error_removal_analysis*.json)

from collections import defaultdict
import json
from os.path import exists

eval_data_list = [
  # ('output/test_data_baseline.json', 'output/error_removal_analysis_baseline.json'),
  # ('output/test_data_t5large.json', 'output/error_removal_analysis_t5large.json'),
  # ('output/test_data_noTFix_100ep.json', 'output/error_removal_analysis_noTFix_100ep.json'),
  # ('output/test_data_no_indent.json', 'output/error_removal_analysis_no_indent.json'),
  # ('output/test_data_t5small_100ep.json', 'output/error_removal_analysis_t5small_100ep.json'),
  # ('output/test_data_baseline_top20.json', 'output/error_removal_analysis_baseline_top20.json'),
  ('output/test_data_baseline_top50.json', 'output/error_removal_analysis_baseline_top50.json'),
  # ('output/test_data_noTFix_100ep_top50.json', 'output/error_removal_analysis_noTFix_100ep_top50.json'),
  # ('output/test_data_t5large_top50.json', 'output/error_removal_analysis_t5large_top50.json'),
  # ('output/test_data_no_indent_top50.json', 'output/error_removal_analysis_no_indent_top50.json'),
  # ('output/test_data_t5small_100ep_top50.json', 'output/error_removal_analysis_t5small_100ep_top50.json'),
]

def calculate_metrics(test_data_json, error_removal_json):  
  count_dict = defaultdict(int)
  # top1_natural_dict = defaultdict(int)
  # top3_natural_dict = defaultdict(int)
  # top5_natural_dict = defaultdict(int)
  topk_dict = defaultdict(lambda: defaultdict(int))

  # Count the exact match from `test_data_json` as error removal
  with open(test_data_json) as f:
    test_data = json.load(f) 
    for d in test_data:
      count_dict[d['linter_report']['rule_id']] += 1
      if d['correct'] and 'no_indent' not in test_data_json and 't5large' not in test_data_json: # and 't5small_100ep_top50' not in test_data_json: 
        # For some models, we don't count the exact match from `test_data_json` as error removal
        for k in [1,3,5,20,50]:
          topk_dict['top-'+str(k)+'_error_removal'][d['linter_report']['rule_id']] += 1

  with open(error_removal_json) as f:
    err_removal = json.load(f) 
    for d in err_removal:      
      try:
        for k in [1,3,5,20,50]:
          try:
            if any(d['pred_top-'+str(i)]['warning_removed'] for i in range(1,k+1)):
              topk_dict['top-'+str(k)+'_error_removal'][d['warning_type']] += 1
          except Exception as e:
            pass
        # if d.get('manual_eval_top1'):
        #   top1_natural_dict[d['warning_type']] += 1
        #   top3_natural_dict[d['warning_type']] += 1
        #   top5_natural_dict[d['warning_type']] += 1
        # if d.get('manual_eval_top3'):
        #   top3_natural_dict[d['warning_type']] += 1
        #   top5_natural_dict[d['warning_type']] += 1
        # if d.get('manual_eval_top5'):
        #   top5_natural_dict[d['warning_type']] += 1
      except:
        pass

  print(test_data_json, error_removal_json)
  sum_check = 0
  
  # Error removal rate for each type
  for w, count in count_dict.items():
    print(w)
    for k in [1,3,5,20,50]:
      try:
        print('    top-'+str(k)+' error removal rate:', topk_dict['top-'+str(k)+'_error_removal'][w]/count*100)
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
    print(k, sum(w_dict.values()), sum(w_dict.values())/len(test_data) * 100)
  # print(sum(sum(w_dict.values()) for w_dict in topk_dict.values()))
  # print('Overall top-1 (natural) error removal rate:', sum(top1_natural_dict.values())/len(test_data)*100)
  # print('Overall top-3 (natural) error removal rate:', sum(top3_natural_dict.values())/len(test_data)*100)
  # print('Overall top-5 (natural) error removal rate:', sum(top5_natural_dict.values())/len(test_data)*100)
  print('count:', len(err_removal))
  print('total:', len(test_data))
  print('sum_check:', sum_check)
  print('--------------------------------------------')


for (test_data, error_removal) in eval_data_list:
  calculate_metrics(test_data, error_removal)