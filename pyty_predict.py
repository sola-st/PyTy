import argparse
import json
import sys

sys.path.append("..")

from transformers import T5ForConditionalGeneration
from transformers import T5Tokenizer
from transformers import set_seed
import torch

from utils import boolean_string
from utils import get_current_time

def get_single_prediction(model, tokenizer, input_text, max_length=256, beam_size=50, num_seq=50):
    # Tokenize the input text
    input_ids = tokenizer.encode(input_text, truncation=True, padding=True, return_tensors='pt').to(model.device)
    # print("input_ids: ", input_ids)
    # Generate predictions
    beam_outputs = model.generate(
        input_ids, 
        max_length=max_length, 
        num_beams=beam_size, 
        num_return_sequences=num_seq,
        early_stopping=False
    )
    # Decode the predictions
    predictions = [tokenizer.decode(output, skip_special_tokens=True) for output in beam_outputs]

    return predictions

# transformers.logging.set_verbosity_info()
set_seed(42)
print("start time: ", get_current_time())

parser = argparse.ArgumentParser()
parser.add_argument("-bs", "--batch-size", type=int, default=1)
parser.add_argument(
    "-mn",
    "--model-name",
    type=str,
    # choices=["t5-small", "t5-base", "t5-large", "t5-3b", "t5-11b"],
    required=True,
)
parser.add_argument(
    "-lm", "--load-model", type=str, default=""
)  #  Checkpoint dir to load the model. Example: t5-small_global_14-12-2020_16-29-22/checkpoint-10
parser.add_argument(
    "-ea", "--eval-all", type=boolean_string, default=False
)  # to evaluate on all data or not
parser.add_argument("-eas", "--eval-acc-steps", type=int, default=1)
# parser.add_argument("-md", "--model-dir", type=str, default="")
parser.add_argument("-et", "--error-type", type=str, default="")
parser.add_argument("-bm", "--beam-size", type=int, default=50) # number of beams to use
parser.add_argument("-seq", "--num-seq", type=int, default=50) # number of seq to generate, must be <= number of beams
parser.add_argument("-f", "--file_path", type=str, required=True, help="Enter the path to the file containing input.")
args = parser.parse_args()

model_name = args.model_name

# Load the tokenizer and the model that will be tested.
tokenizer = T5Tokenizer.from_pretrained(args.load_model)
print("Loaded tokenizer from directory {}".format(args.load_model))
model = T5ForConditionalGeneration.from_pretrained(args.load_model)
print("Loaded model from directory {}".format(args.load_model))
model.to(f"cuda:{torch.cuda.current_device()}")
model.resize_token_embeddings(len(tokenizer))
model.eval()

with open(args.file_path, 'r') as f:
    data = json.load(f)
    rule_id = data['rule_id']
    message = data['message']
    warning_line = data['warning_line']
    source_code = data['source_code']

input_text = (
    "fix "
    + rule_id
    + " " 
    + message
    + " " 
    + warning_line
    + ":\n"
    + source_code
    + " </s>"
)

predictions = get_single_prediction(model, tokenizer, input_text, max_length=256, beam_size=50, num_seq=50)

# Print the predictions
print("Input Text:", input_text)
print("Predictions:")
for i, pred in enumerate(predictions):
    print(repr(f"      \"{i}\": \"{pred}\""))

