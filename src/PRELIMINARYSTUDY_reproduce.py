import subprocess
import os


# Figure 4a
subprocess.run(["python3", "plot4a.py"], cwd='./src/preliminary_study_dataset')

print("\n\n===========================\n\n")
# Figure 4b
subprocess.run(["python3", "plot4b.py"], cwd='./src/preliminary_study_dataset')

print("\n\n===========================\n\n")
# Figure 4c
subprocess.run(["python3", "plot4c.py"], cwd='./src/preliminary_study_dataset')

print("\n\n===========================\n\n")
# Figure 2
subprocess.run(["python3", "plot2.py"], cwd='./src/preliminary_study_dataset')

print("\n\n===========================\n\n")
print("\n\nYou can find all the generated plots and the data collected in ./src/preliminary_study_dataset. They could have different colours, but same numbers.\n\n")
