import subprocess
import os

# Table 1, Column Error Removal
subprocess.run(["python3", "calculate_topk_error_removal_PyTy.py"], cwd='./src')

print("\n\n===========================\n\n")
# Table 1, Column Exact Match 
subprocess.run(["python3", "calculate_topk_exact_match_PyTy.py"], cwd='./src')

