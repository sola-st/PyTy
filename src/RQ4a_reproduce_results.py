import subprocess
import os


print("\n\n===========================\n\n")
# Table 2, Column Error Removal (%)
subprocess.run(["python3", "calculate_topk_openai_exact_match.py"], cwd='./src/eval_code/LLM')


print("\n\n===========================\n\n")
# Table 2, Column Exact Match (%)
subprocess.run(["python3", "calculate_topk_openai_error_removal.py"], cwd='./src/eval_code/LLM')

