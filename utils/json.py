import json
from pathlib import Path

__all__ = ["read_json", "write_json", "json_unset", "json_upsert"]

from typing import List, Dict, Union, Any


def get_path():
    """
    A function to get the current path to bot.py
    Returns:
     - cwd (string) : Path to bot.py directory
    """
    cwd = Path(__file__).parents[1]
    cwd = str(cwd)
    return cwd


def read_json(filename):
    """
    A function to read a json file and return the data.
    Params:
     - filename (string) : The name of the file to open
    Returns:
     - data (dict) : A dict of the data in the file
    """
    cwd = get_path()
    with open(cwd + '/assets/' + filename + '.json', 'r') as file:
        data = json.load(file)
    return data


def write_json(data, filename):
    """
    A function used to write data to a json file
    Params:
     - data (dict) : The data to write to the file
     - filename (string) : The name of the file to write to
    """
    cwd = get_path()
    with open(cwd + '/assets/' + filename + '.json', 'w') as file:
        json.dump(data, file, indent=4)


def json_unset(data: List[str], filename):
    # Check if its actually a Dictionary
    json_data = read_json(filename)
    for value in data:
        if json_data and value in json_data:
            json_data.pop(value)
    write_json(json_data, filename)


def json_upsert(data: Dict[str, Union[str, int, List[Any], Dict[Any, Any]]], filename):
    config = read_json(filename)
    if config:
        for key, value in data.items():
            config[key] = value
    else:
        config = data
    write_json(config, filename)
