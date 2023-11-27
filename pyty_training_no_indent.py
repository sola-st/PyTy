from datetime import datetime
import argparse
import os
import sys
import numpy as np

sys.path.append("..")

from transformers import Seq2SeqTrainer
from transformers import Seq2SeqTrainingArguments
from transformers import T5Config
from transformers import T5ForConditionalGeneration
from transformers import T5Tokenizer
from transformers import set_seed
# from datasets import load_metric

import torch

from data_reader_pyre_no_indent import GetDataAsPython
from prepare_data import create_data
from prepare_data import create_dataset
from prepare_data import extract_warning_types
from utils import boolean_string
from utils import get_current_time

# transformers.logging.set_verbosity_info()
# metric = load_metric('accuracy')
set_seed(42)
print("start time: ", get_current_time())

parser = argparse.ArgumentParser()
parser.add_argument("-e", "--epochs", type=int, default=1)
parser.add_argument("-bs", "--batch-size", type=int, default=1)
parser.add_argument("-lr", "--learning-rate", type=float, default=1e-4)
parser.add_argument("-gcv", "--gradient-clip-val", type=float, default=0.0)
parser.add_argument("-wd", "--weight-decay", type=float, default=0)
parser.add_argument(
    "-mn",
    "--model-name",
    type=str,
    # choices=["t5-small", "t5-base", "t5-large", "t5-3b", "t5-11b"],
    required=True,
)
parser.add_argument("-eas", "--eval-acc-steps", type=int, default=1)
parser.add_argument("-md", "--model-dir", type=str, default="")
parser.add_argument("-et", "--error-type", type=str, default="")
parser.add_argument("-stl", "--save-total-limit", type=int, default=-1)
parser.add_argument("-pt", "--pre-trained", type=boolean_string, default=True)
args = parser.parse_args()

# Create job directory
model_name = args.model_name
if args.model_dir != "":
    model_directory = args.model_dir
else:
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y_%H-%M-%S")
    model_directory = "t5global" + "_" + dt_string
    model_directory = model_name + "_global_" + dt_string

os.makedirs(model_directory)
with open(os.path.join(model_directory, "commandline_args.txt"), "w") as f:
    f.write("\n".join(sys.argv[1:]))

# Read and prepare data
data = GetDataAsPython("Input/")
# data_eslint = GetDataAsPython("data_and_models/data/data_autofix_tracking_eslint_final.json")
# data += data_eslint
all_warning_types = extract_warning_types(data)
if args.error_type != "":
    all_warning_types = [args.error_type]
print(all_warning_types)
(
    train_inputs,
    train_labels,
    val_inputs,
    val_labels,
    test_inputs,
    test_labels,
    train_info,
    val_info,
    test_info,
) = create_data(data, all_warning_types, include_warning=True, model_name=model_name)

# Create the tokenizer and the model
tokenizer = T5Tokenizer.from_pretrained(
    model_name,
)
# add newline, indent, dedent because it is part of python syntax
tokenizer.add_tokens(["{", "}", ">", "\\", "^"])#, "\n", "<IND>", "<DED>"]) 
# tokenizer.add_tokens(["{", "}", ">", "\\", "^"]) 
tokenizer.save_pretrained(model_directory)
if args.pre_trained:
    model = T5ForConditionalGeneration.from_pretrained(model_name, return_dict=False)
else:
    print("Training from scratch")
    config = T5Config.from_pretrained(model_name)
    model = T5ForConditionalGeneration(config)
model.parallelize()
model.resize_token_embeddings(len(tokenizer))
print("Models parameters: ", model.num_parameters())

train_dataset = create_dataset(
    train_inputs, train_labels, tokenizer, pad_truncate=True, max_length=128
)
val_dataset = create_dataset(val_inputs, val_labels, tokenizer, pad_truncate=True)
# Training arguments
training_args = Seq2SeqTrainingArguments(
    output_dir=model_directory,
    num_train_epochs=args.epochs,
    per_device_train_batch_size=args.batch_size,
    per_device_eval_batch_size=args.batch_size,
    warmup_steps=500,
    weight_decay=args.weight_decay,
    logging_dir=model_directory,
    logging_steps=100,
    do_eval=True,
    evaluation_strategy="epoch",
    learning_rate=args.learning_rate,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    save_total_limit=args.epochs if args.save_total_limit == -1 else args.save_total_limit,
    eval_accumulation_steps=args.eval_acc_steps,  # set this lower, if testing or validation crashes
    disable_tqdm=False,
    predict_with_generate=True,  # never set this to false.
    seed=42,  # default value
    # report_to=["tensorboard", "wandb"], # log to tensorboard and wandb
)

# # Function to compute accuracy during training
# def compute_accuracy(eval_pred):
#     output_ids, target_ids = eval_pred
#     # return metric.compute(predictions=predictions, references=labels)
#     target_max_length = 256
#     # pad 0 until 256 tokens for each sample
#     target_ids = np.pad(
#         target_ids, ((0, 0), (0, target_max_length - target_ids.shape[1])), mode="constant"
#     )    
#     output_ids = np.pad(
#         output_ids, ((0, 0), (0, target_max_length - output_ids.shape[1])), mode="constant"
#     )
#     output_ids = np.delete(output_ids, 0, axis=1) # remove 1st element for each sample
#     output_ids = np.insert(output_ids, target_max_length - 1, 0, axis=1) # insert 0 at the end for each sample
#     print('target_ids')
#     for t in target_ids.tolist():
#         print(tokenizer.decode(t, skip_special_tokens=True))
#     print('output_ids')
#     for o in output_ids.tolist():
#         print(tokenizer.decode(o, skip_special_tokens=True))    
#     correct_counter = np.sum(np.all(np.equal(target_ids, output_ids), axis=1)) # (254,171) (254,20) -> (254,171) (254,256)
#     total_counter = len(output_ids)
#     return {'accuracy': correct_counter/total_counter}

# Create trainer
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    optimizers=[torch.optim.Adam(params=model.parameters(), lr=args.learning_rate), None],
    tokenizer=tokenizer,
    # compute_metrics=compute_accuracy,
)

trainer.train()
print("end time: ", get_current_time())
