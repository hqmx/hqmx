import json
import os

conversions_json_path = "converter/frontend/_scripts/subtitle-conversions.json"
# Languages are not used for this specific URL format as requested by the user
# languages = [
#   'en', 'ko', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'zh',
#   'ar', 'hi', 'nl', 'sv', 'pl', 'tr', 'vi', 'th', 'id', 'he', 'cs'
# ]
base_url_prefix = "https://hqmx.net/converter"

try:
    with open(conversions_json_path, 'r', encoding='utf-8') as f:
        conversions = json.load(f)
except FileNotFoundError:
    print(f"Error: {conversions_json_path} not found.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {conversions_json_path}.")
    exit(1)

urls = []
for conversion in conversions:
    from_format = conversion['from']
    to_format = conversion['to']
    # URL Format: https://hqmx.net/converter/{from}-to-{to}
    url_path = f"/{from_format}-to-{to_format}"
    full_url = f"{base_url_prefix}{url_path}"
    urls.append(full_url)

for url in urls:
    print(url)