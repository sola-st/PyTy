# Automatic Program Repair for Python Type Errors
Contains script to extract the error fixing code hunks in a commit.

## Setup
- Start a venv
- Install requirements via `pip install -r requirements.txt` (`pyre` should be included) and `watchman`
- Run a script to kill pyre servers every N minutes to stop it from occupying system resources if it didn't terminate successfully.

## What does it do?
Prerequisite:
- You should have a list of JSON files with these fields: 
  - `project`: repo's name on GitHub
  - `b_commit`: commit where the type warning is fixed
  - `parent_warnings`: list of `pyre` warnings before `b_commit`
  - `warnings`: list of `pyre` warnings after `b_commit`
- You should have cloned the GitHub repo of all the `project` in your JSON files

Given a pyre warning, the script will search which hunks in a commit fix the error (we call it the minimal patch) via delta-debugging (dd).

Input:
- A pyre warning that is fixed after a commit
- Python code (file) before commit
- Python code (file) after commit

Ouput:
- Hunks that fix the warning, with some metadata

The delta (i.e. diff of the file before and after commit) is computed using the [difflib](https://docs.python.org/3/library/difflib.html) in unidiff format. Patching is done by using a modified version of [python-patch](https://github.com/techtonik/python-patch).

The [diff-match-patch Python library](https://github.com/google/diff-match-patch) is not suitable as it has a rolling context and is character-based. Patch failures are often during our experiment using it.

## File organization
`Manual_eval_DD.csv`: Manual evaluation of delta-debugging output. (Evaluation RQ1)

`random_samples_PyTy_final.txt`: Randomly selected samples for manual evaluation. (Evaluation RQ1)

`pyreDD.py`: Run this script to do delta-debugging with pyre warnings.

`DD.py`: The delta-debugging library from: [dd-py3](https://github.com/mdrafiqulrabin/dd-py3). 

`run_dd_on_dataset.py`: Script will run `pyreDD.py` on the input dataset (commit-warnings) in N threads. Output a json that contains the minimal hunks to fix the corresponding warnings.

`tokenize_code_indent.py`: Preprocess Python source code for APR. Add indentation tokens.

`run_dd_on_selected_data.py`: Same as `run_dd_on_dataset.py` but will not output. Only meant for debugging on some selected data.

`random_select.py`: Randomly select 100 output where the a single minimal hunk is found. Each output is from a different commits.

`patch_modified.py`: A modified version of [python-patch] for patching.

`count_data.py`: Output a data analysis of the output dataset.

`patch_TFix_data.py`: (Should not need to run this.) Script to patch data: update whether it fits the our model or not. 

## How to run
`python run_dd_on_dataset.py`

Note: this involves multiple commad line calls like `git checkout`, `watchman watch .` and `pyre incremental`, which could be resource intensive.

## Reference
- The delta-debugging library used is from: [dd-py3](https://github.com/mdrafiqulrabin/dd-py3), which updates the core modules ([DD.py](https://www.st.cs.uni-saarland.de/dd/DD.py) and [MyDD.py](https://www.st.cs.uni-saarland.de/dd/MyDD.py)) from https://www.st.cs.uni-saarland.de/dd/ to run delta-debugging in Python 3 instead of Python 2.
- [difflib](https://docs.python.org/3/library/difflib.html)
- [python-patch](https://github.com/techtonik/python-patch)
