# scraper/json_writer.py

import os
import json

def write_to_json(grouped_data, json_path="data/data.json"):
    final_output = []

    for category, contents in grouped_data.items():
        pages = [
            {"url": content.get("source", "Unknown"), "content": content.get("text", "")}
            for content in contents
        ]
        final_output.append({"category": category, "pages": pages})

    # Load existing JSON
    existing_data = []
    if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except:
            existing_data = []

    # Merge data
    existing_dict = {e["category"]: e for e in existing_data}
    for entry in final_output:
        cat = entry["category"]
        if cat in existing_dict:
            existing_urls = {p["url"]: p for p in existing_dict[cat]["pages"]}
            for p in entry["pages"]:
                existing_urls[p["url"]] = p
            existing_dict[cat]["pages"] = list(existing_urls.values())
        else:
            existing_dict[cat] = entry

    # Write final JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(list(existing_dict.values()), f, indent=2, ensure_ascii=False)

    print(f"✅ Data written to {json_path}")
