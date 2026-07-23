import json
import os

def read_json(filename):
    """
    Read a JSON file from the cache directory.
    
    Args:
        filename (str): Name of the JSON file to read (without .json extension)
    
    Returns:
        dict: Parsed JSON data or None if file not found
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(project_root, 'cache')
    
    file_path = os.path.join(cache_dir, f"{filename}.json")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Warning: {file_path} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def write_json(filename, data):
    """
    Write data to a JSON file in the cache directory.
    
    Args:
        filename (str): Name of the JSON file (without .json extension)
        data (dict or list): Data to be written to the file
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    cache_dir = os.path.join(project_root, 'cache')
    
    os.makedirs(cache_dir, exist_ok=True)
    
    file_path = os.path.join(cache_dir, f"{filename}.json")
    
    try:
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")