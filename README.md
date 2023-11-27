
# PyTy: Statically Repairing Type Errors in Python 
PyTy is an automated program repair approach specifically for Python type errors. PyTy uses a learning-based model which we train on a Python dataset of type error fixes.

## Based on TFix
This implentation is based on [TFix: Learning to Fix Coding Errors with a Text-to-Text Transformer
](https://github.com/eth-sri/TFix). The TFix paper can be found under [this](https://www.semanticscholar.org/paper/TFix%3A-Learning-to-Fix-Coding-Errors-with-a-Berabi-He/0505f17c4052366cbc4fad99150d3542edf85faa) and
[this link](https://files.sri.inf.ethz.ch/website/papers/icml21-tfix.pdf).

## Setup

Create a virtual environment then install the requirements.
```
python3 -m venv venv_pyty
source venv_pyty/bin/activate
pip install -r requirements.txt
```
<br/>

## Dataset and Models
- Python Type Fixes Dataset: `unzip Input.zip`.
- TFix models: Download `data_and_models` from [TFix](https://github.com/eth-sri/TFix)

<br/>

## Configuration

The main scripts are `pyty_training.py` and `pyty_testing.py`.

`pyty_training_no_indent.py` and `pyty_testing_no_indent.py` are for models without Python preprocessing.

The `pyty_training.py` has the following arguments:

Required arguments:

```
 -mn --model-name   Name of the model. Choices: [t5-small, t5-base, t5-large, t5-3b, t5-11b]
```

Optional arguments:

| Parameter                | Default | Description                                                          |
| :----------------------- | :-----: | :------------------------------------------------------------------- |
| -e --epochs              |    1    | Number of epochs to fine-tune the model                              |
| -bs --batch-size         |    1    | Batch size to be used in fine-tuning                                 |
| -lr -–learning-rate      |  1e-4   | The initial learning rate for fine-tuning                            |
| -gcv --gradient-clip-val |   0.0   | The maximum allowed norm of the gradient (0.0 means no clipping)     |
| -wd --weight-decay       |   0.0   | The strength of adding L2-loss to the fine-tuning loss               |
| -eas --eval-acc-steps    |    1    | Number of accumulation samples during evaluation and testing         |
| -md --model-dir          |   ''    | Directory name for the model to save checkpoints and testing results |
| -et --error-type         |   ''    | The error type for fine-tuning or testing                            |
| -stl --save-total-limit  |   -1    | Maximum number of checkpoints to save                                |
| -pt --pre-trained        |  True   | Whether to use the pre-training model or not                         |

<br/>
<br/>

The `pyty_testing.py` has the following arguments:
Required arguments:

```
 -lm --load-model   Path to the model's checkpoint that will be tested.
```

Optional arguments:

| Parameter             | Default | Description                                                          |
| :-------------------- | :-----: | :------------------------------------------------------------------- |
| -bs --batch-size      |    1    | Batch size to be used in fine-tuning                                 |
| -lm -–load-model      |   ''    | The path to a trained model to run testing                           |
| -eas --eval-acc-steps |    1    | Number of accumulation samples during evaluation and testing         |
| -md --model-dir       |   ''    | Directory name for the model to save checkpoints and testing results |
| -et --error-type      |   ''    | The error type for fine-tuning or testing                            |
| -bm --beam-size       |   50    | Number of beam to use for generating fixes                           |
| -seq --num-seq        |   50    | Number of predictions to be generated, must be <= beam-size          |

The testing results consist of two files `first_accs.txt` and `test_data.json`, and are saved in the model directory. 

`first_accs.txt` reports the exact match accuracy for each error type and `test_data.json` stores the PyTy's output fixes in JSON format.

<br/>

## Reproducing the experiments (Full PyTy and Ablation models)
For top-50 predictions only. For top-1 and top-5, please use `-bm 5` and `-seq 5`.

Full PyTy:
- Training
`python pyty_training.py -e 30 -bs 32 -mn data_and_models/models/t5base -md t5base_final`
- Testing
`python pyty_testing.py -mn t5base_final -lm t5base_final/checkpoint-1190 -md t5base_final_test`

PyTy without pre-training:
- Training
`python pyty_training.py -e 100 -bs 32 -mn t5-base -md t5base_no_pt`
- Testing
`python pyty_testing.py -mn t5base_no_pt -lm t5base_no_pt/checkpoint-2240 -md t5base_no_pt_test`

TFix without fine-tuning:
- Testing
`python pyty_testing_no_indent.py -mn t5large -lm data_and_models/models/t5large -md t5large_test`

PyTy without preprocessing:
- Training
`python pyty_training_no_indent.py -e 30 -bs 32 -mn data_and_models/models/t5base -md t5base_final_no_indent`
- Testing
`python pyty_testing_no_indent.py -mn t5base_final_no_indent -lm t5base_final_no_indent/checkpoint-1050 -md t5base_final_no_indent_test`

PyTy with small TFix:
- Training
`python pyty_training.py -e 100 -bs 32 -mn data_and_models/models/t5small -md t5small_final`
- Testing
`python pyty_testing.py -mn t5small_final -lm t5small_final/checkpoint-3290 -md t5small_final_test`

Running `pyty_testing.py` outputs the exact match accuracy of top-1 predictions and outputs the predictions up to top-k (in `test_data.json`).

<br/>

## Running PyTy on a type error and code snippet
`pyty_predict.py` is used to run PyTy on a type error and code snippet. The input is a JSON file with the following format:
``` 
{
  "rule_id": "Unbound name [10]",
  "message": " Name `y_test` is used but not defined in the current scope.",
  "warning_line": "    results = mean_squared_error(y_test, model.predict(X_test))",
  "source_code": "    # Run some test predictions\n    results = mean_squared_error(y_test, model.predict(X_test))\n"
}
```
An example input file is provided in `predict_sample_input.json`. To run PyTy on the sample input, run the following command:
`python pyty_predict.py -mn t5base_final -lm t5base_final/checkpoint-1190 -f predict_sample_input.json`

## Evaluation scripts

`check_error_all.py`: (Prerequisite: Cloned GitHub repo for each samples) Runs on all `pyty_testing.py` output (`test_data.json`). Replaces the original source code with the prediction output, and run `pyre` to check if the error in the sample is removed.

`check_error_not_exact.py`: (Prerequisite: Cloned GitHub repo for each samples) Same as a `check_error_all.py`, but only runs on non-exact match (i.e., `correct` field in `test_data.json` is false.).

`calculate_topk_error_removal.py`: Calculate the top-k error removal rate on `test_data.json` and `error_removal_analysis_*.json` (output from `check_error_all.py`/`check_error_not_exact.py`).

`calculate_topk_exact_match.py`: Calculate the top-k exact match rate on `test_data.json`.

## Evaluation scripts for type fixes in the wild

`eval_code/` contains code to run and evaluate PyTy on type errors found in the wild. The scripts are similar to the above section, but in this case we adapt the code (`evalpytytesting.py`) to find new type errors in the same repositories of PyTyDefects and manually open pull requests with the suggested fixes. (Section 6.2.4 in the paper).

## Comparison with PyTER and LLMs

The `eval_code/eval_PyTER_comparison.py` script checks all type errors in our test dataset against the repair templates by PyTER (Oh and Oh, FSE'22).

The `eval_code/eval_inspect_fixes.py` and `output/manual_commit_inspection.json` files document how we inspected fixes in our test dataset to determine the problem had manifested via a static error or via a `TypeError` runtime exception.

The folder `evalcode/OpenAI` contains the scripts to run the evaluation with OpenAI models. The main scripts are:

`chatgpt.py` queries the models to get the top 50 predictions for the python type errors in the testset. 
`calculate_topk_error_removal.py` checks if the type fixes are correct using the type checker pyre before and after the edit.
`final_statistics.py` computes the overall results for Table 3 in the paper.
