import json, os

def read_json(filename):
    if os.path.exists(f"cache/{filename}.json"):
        with open(f"cache/{filename}.json", 'r') as f:
            return json.load(f)
    else:
         print(F"No file named {filename}.json found")

def write_json(filename, data):
    with open(f"cache/{filename}.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)