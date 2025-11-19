# scraper/post_processing.py

import os
import re
from collections import defaultdict
import json
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from scraper.json_writer import write_to_json
from scraper.utils import ensure_folder
from config.settings import OUTPUT_BASE, JSON_FILE, LINK_FILENAME


def create_category_folder():
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for key, value in data.items():
        folder_path = os.path.join(OUTPUT_BASE, key)
        ensure_folder(folder_path)

        file_path = os.path.join(folder_path, LINK_FILENAME)
        with open(file_path, "w", encoding="utf-8") as txt:
            for link in value.get("links_found", []):
                txt.write(link + "\n")

        print(f"[OK] Created {file_path}")


def visit_per_projects(folder):
    for root, dirs, _ in os.walk(folder):
        for dir_name in dirs:
            folder_path = os.path.join(root, dir_name)
            grouped_data = defaultdict(list)

            try:
                for file in os.listdir(folder_path):
                    if not file.endswith(".txt"):
                        continue

                    urls = open(os.path.join(folder_path, file), "r", encoding="utf-8") \
                        .read().splitlines()

                    loader = SeleniumURLLoader(
                        urls=urls)
                    docs = loader.load()

                    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    documents = splitter.split_documents(docs)

                    for doc in documents:
                        grouped_data[dir_name].append({
                            "text": re.sub("\n\n+", "\n", doc.page_content),
                            "source": str(doc.metadata.get("source", "Unknown"))
                        })
            finally:
                write_to_json(grouped_data)
