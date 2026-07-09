from WebCrawler import crawl
import os
import json

# TODO: Organize results
# TODO: Apply results directly to Google Sheets
# TODO: Make headless once finished debugging
# TODO: Speed up getting code from email

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    config = load_config(config_path)
    results = crawl(config)
    print("Results successfully obtained")

if __name__ == "__main__":
    main()