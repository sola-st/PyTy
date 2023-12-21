import subprocess
import os

# Table 2, Column Error Removal 
subprocess.run(["python3", "final_statistics_davinci.py"], cwd='./output/')
print('\n')
subprocess.run(["python3", "final_statistics_gpt35.py"], cwd='.')
print('\n')
subprocess.run(["python3", "final_statistics_gpt4_error_removal.py"], cwd='.')

print("\n\n===========================\n\n")



