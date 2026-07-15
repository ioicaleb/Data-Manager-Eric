import json
import os
from pathlib import Path

def read_json(filename):
    """
    Read and parse JSON data from a file.
    
    Args:
        filename (str): Name of the JSON file (without .json extension)
        
    Returns:
        dict or list: Parsed JSON data if file exists, None otherwise
        
    Note:
        Files are expected to be in the 'cache' directory
    """
    file_path = Path(f"cache/{filename}.json")
    
    # Check if file exists
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from {filename}.json: {e}")
            return None
        except Exception as e:
            print(f"Error reading file {filename}.json: {e}")
            return None
    else:
        print(f"No file named {filename}.json found")
        return None

def write_json(filename, data):
    """
    Write data to a JSON file.
    
    Args:
        filename (str): Name of the JSON file (without .json extension)
        data (dict or list): Data to be written to the file
        
    Note:
        Files will be created in the 'cache' directory
    """
    # Ensure cache directory exists
    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    
    file_path = cache_dir / f"{filename}.json"
    
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f"Successfully wrote data to {filename}.json")
    except Exception as e:
        print(f"Error writing to {filename}.json: {e}")