import subprocess
import os

# Table 2, Column Exact Match 
subprocess.run(["python3", "final_statistics_gpt4.py"], cwd='.')

print("\n\n===========================\n\n")
# Table 2, Column Error Removal 
subprocess.run(["python3", "final_statistics_gpt35.py"], cwd='.')
