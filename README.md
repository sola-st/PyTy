# PyTy: Repairing Static Type Errors in Python
PyTy is an automated program repair approach specifically designed for Python type errors. PyTy utilizes a learning-based model trained on a dataset of Python type error fixes called PyTyDefects.

## Purpose
Submission for ICSE 2024 Artifact:
- Available Badge: We provide the artifact with a permanent DOI from Zenodo and also maintain a public GitHub repository for the project.
- Reusable Badge: We describe how to reproduce the paper's results using Docker and use the tool to fix new bugs in other repositories.

## Provenance
- The source code and data are publicly available on Zenodo and GitHub: DOI (TODO) and https://github.com/sola-st/PyTy.

- As a timestamp, the last GitHub commit before submitting the artifact is: (TODO).

## Data
We also include the dataset we collected, named PyTyDefects. The full dataset in JSON format is available in the folder: ./src/Input. Each JSON file represents (TODO: explain).

## Setup
- Hardware: To run the script in "FAST MODE", a normal computer suffices. For "SLOW MODE", we used (and recommend) a server with 250 GB RAM, 48 Intel Xeon CPU cores with 2.2Ghz and an NVIDIA Telta V100 GPU.
- Software: 
  - Ubuntu OS 
  - Docker ([installation instructions](https://docs.docker.com/engine/install/ubuntu/))

## Usage
0. Enter the `PyTy` directory, i.e., the directory of this repository.

1. Setup of Docker to not use sudo for each command:
  ```
      sudo usermod -aG docker $USER
      newgrp docker
  ```
 
2. Build the Docker image:
  ```
      docker build -t icse2024 .
  ```
3. Choose between FAST MODE, which computes the final results from pre-computed intermediate results and should take less than 30 minutes, and SLOW MODE, which trains the neural models and may take several hours, depending on hardware.
  - FAST MODE (less than 30 minutes):

    - Evaluation:
      - RQ1: Inspect `./src/eval_code/CSV/RQ1.csv`, which contains the manual labels of the two annotators before their discussion (Section 6.1.2 of the paper).
      - RQ2: Run `docker run icse2024 python src/RQ2_reproduce_results.py`, which produces Table 1 of the paper.
      - RQ3: Run `docker run icse2024 python src/RQ3_reproduce_results.py`, which produces Table 2 (first and last block of the table) of the paper.
      - RQ4a: Run `docker run icse2024 python src/RQ4a_reproduce_results.py`, which produces Table 2 (second block of the table) of the paper.
      - RQ4b.1: See `./src/output/manual_commit_inspection.json`, which contains the 30 manually inspected fixes in our test set. The 'comment' field contains an explanation of our assessment.
      - RQ4b.3: manually look at the file `./src/eval_code/CSV/RQ4b3.csv`, there is the manual analysis of PyTer dataset
  
    
    - Preliminary study:
      - run from the root: `docker run -v $(pwd)/src/preliminary_study_dataset:/src/preliminary_study_dataset icse2024 python src/PRELIMINARYSTUDY_reproduce.py`
  

  - SLOW MODE (Several hours depending on hardware):
    - Python Type Fixes Dataset: `unzip ./src/Input.zip`.
    - TFix models: Download `data_and_models` in `./src/` from [TFix](https://github.com/eth-sri/TFix).
  
      For top-50 predictions only. For top-1 and top-5, please use `-bm 5` and `-seq 5`.
  
      Full PyTy:
      - Training
        `docker run icse2024 python ./src/pyty_training.py -e 30 -bs 32 -mn data_and_models/models/t5base -md t5base_final`
      - Testing
        `docker run icse2024 python ./src/pyty_testing.py -mn t5base_final -lm t5base_final/checkpoint-1190 -md t5base_final_test`
  
      PyTy without pre-training:
      - Training
      `docker run icse2024 python ./src/pyty_training.py -e 100 -bs 32 -mn t5-base -md t5base_no_pt`
      - Testing
      `docker run icse2024 python ./src/pyty_testing.py -mn t5base_no_pt -lm t5base_no_pt/checkpoint-2240 -md t5base_no_pt_test`
  
      TFix without fine-tuning:
      - Testing
      `docker run icse2024 python ./src/pyty_testing_no_indent.py -mn t5large -lm data_and_models/models/t5large -md t5large_test`
  
      PyTy without preprocessing:
      - Training
      `docker run icse2024 python ./src/pyty_training_no_indent.py -e 30 -bs 32 -mn data_and_models/models/t5base -md t5base_final_no_indent`
      - Testing
      `docker run icse2024 python ./src/pyty_testing_no_indent.py -mn t5base_final_no_indent -lm t5base_final_no_indent/checkpoint-1050 -md t5base_final_no_indent_test`
  
      PyTy with small TFix:
      - Training
      `docker run icse2024 python ./src/pyty_training.py -e 100 -bs 32 -mn data_and_models/models/t5small -md t5small_final`
      - Testing
      `docker run icse2024 python ./src/pyty_testing.py -mn t5small_final -lm t5small_final/checkpoint-3290 -md t5small_final_test`
  
      Running `docker run icse2024 ./src/python pyty_testing.py` outputs the exact match accuracy of top-1 predictions and outputs the predictions up to top-k (in `test_data.json`).
  
      Now you can run all the instructions above in the section 'FAST MODE'.
