from datetime import datetime
import json
import os
from typing import Dict, List

from data_reader import DataPoint


def boolean_string(s: str) -> bool:
    if s not in {"False", "True"}:
        raise ValueError("Not a valid boolean string")
    return s == "True"


def get_current_time() -> str:
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    return current_time


def compute_dict_average(dict: Dict) -> float:
    # empty dictionary, return 0
    if not dict:
        return 0

    total = 0
    N = 0
    for key, value in dict.items():
        total += value
        N += 1
    return total / N


def check_test_alignment(
    test_inputs: Dict[str, str], test_info: Dict[str, List[DataPoint]]
) -> None:
    for warning in test_inputs:
        inputs = test_inputs[warning]
        infos = test_info[warning]
        for i, code in enumerate(inputs):
            assert code == infos[i].GetT5Representation(True)[0], "something wrong! stop it!"

def get_project_names(directory):
    """
    Reads all files in a directory and returns a set of file names.
    """
    file_names = {}
    for file_name in os.listdir(directory):
        if file_name.endswith(".json"):
            # normalized_project_name = file_name.replace("dd_out_", "").rsplit("_",1)[0]
            with open(directory+'/'+file_name, 'r') as f:
                data = json.load(f)
                project_name = str(data[0]['project'])
                file_names[project_name.replace('/','-')] = project_name
    return file_names
