import subprocess
import os

# Table 2, Column Exact Match 
subprocess.run(["python3", "final_statistics.py"], cwd='.')
print('\n')
subprocess.run(["python3", "final_statistics_35exactmatch.py"], cwd='.')
print('\n')
subprocess.run(["python3", "final_statistics_gpt4.py"], cwd='.')


