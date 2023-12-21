# PyTy: Statically Repairing Type Errors in Python
PyTy is an automated program repair approach specifically designed for Python type errors. PyTy utilizes a learning-based model trained on a dataset of Python type error fixes.

## Purpose
Submission for:
- Available Badge: We provide the artifact with a permanent DOI from Zenodo and also maintain a public GitHub repository for the project.
- Reusable Badge: We describe how to reproduce the paper's results and use the tool to fix new bugs in other repositories.

## Provenance
- The source code and data are publicly available on Zenodo and GitHub: DOI and https://github.com/sola-st/PyTy.

- As a timestamp, the last GitHub commit before submitting the artifact is.

## Data
We also include the dataset we collected, named PyTyDefects. It is available in the folder: src/Input.

## Setup
- Hardware: To run the script in "fast mode", a normal computer suffices. For "slow mode", we used (and recommend) a 48-core server with 64GB of RAM.
- Software: Ubuntu OS and Python 3.5+, along with the Python packages in ./requirements.txt.

## Usage
- FAST MODE:

  - Evaluation:
    - RQ1: look at the file `./src/eval_code/CSV/RQ1.csv`, there is the manual labels of the two annotators before their discussion, in the paper Section 6.1.2.
    - RQ2: run from the root: `python3 src/RQ2_reproduce_results.py` and compare it with Table 1 in page 7 of ./paper.pdf
    - RQ3: run from the root: `python3 src/RQ3_reproduce_results.py` and compare it with Table 2 (first and last block of the table) in page 9 of ./paper.pdf
    - RQ4a: run from the root: `python3 src/RQ4a_reproduce_results.py` and compare it with Table 2 (second block of the table) in page 9 of ./paper.pdf
    - RQ4b.1 and RQ4b.2: look at the file `./src/output/manual_commit_inspection.json`, with the label 'comment' for each fix
    - RQ4b.3: look at the file `./src/eval_code/CSV/RQ4b3.csv`, there is the manual analysis of PyTer dataset

  
  - Preliminary study:
    - run from the root: `python3 src/PRELIMINARYSTUDY_reproduce.py`

- SLOW MODE:
  - Create a virtual environment and install the requirements.

      ```
      python3 -m venv venv_pyty
      source venv_pyty/bin/activate
      pip install -r requirements.txt
      ```

  
  - Python Type Fixes Dataset: `unzip Input.zip`.
  - TFix models: Download `data_and_models` from [TFix](https://github.com/eth-sri/TFix).

    For top-50 predictions only. For top-1 and top-5, please use `-bm 5` and `-seq 5`.

    Full PyTy:
    - Training
      `python pyty_training.py -e 30 -bs 32 -mn data_and_models/models/t5base -md t5base_final`
    - Testing
      `python pyty_testing.py -mn t5base_final -lm t5base_final/checkpoint-1190 -md t5base_final_test`

- EXTRA MODE:

  `pyty_predict.py` is used to run PyTy on any type error and code snippet. The input is a JSON file with the following format:

    ``` 
    {
      "rule_id": "Unbound name [10]",
      "message": " Name `y_test` is used but not defined in the current scope.",
      "warning_line": "    results = mean_squared_error(y_test, model.predict(X_test))",
      "source_code": "    # Run some test predictions\n    results = mean_squared_error(y_test, model.predict(X_test))\n"
    }
    ```
  An example input file is provided in `predict_sample_input.json`. To run PyTy on the sample input, use the following command:
  `python pyty_predict.py -mn t5base_final -lm t5base_final/checkpoint-1190 -f predict_sample_input.json`

