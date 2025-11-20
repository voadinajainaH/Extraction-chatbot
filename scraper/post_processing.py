# scraper/post_processing.py

import os
import re
import shutil
from collections import defaultdict
import json
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from scraper.json_writer import write_to_json
from scraper.utils import ensure_folder
from config.settings import OUTPUT_BASE, JSON_FILE, LINK_FILENAME

def clear_output_base():
    """Supprime uniquement le contenu de OUTPUT_BASE (dossiers + fichiers)."""
    if not os.path.exists(OUTPUT_BASE):
        os.makedirs(OUTPUT_BASE)
        return

    for item in os.listdir(OUTPUT_BASE):
        item_path = os.path.join(OUTPUT_BASE, item)

        if os.path.isdir(item_path):
            shutil.rmtree(item_path)  # supprimer un dossier
        else:
            os.remove(item_path)      # supprimer un fichier



def create_category_folder():
    clear_output_base()

    # ---- LOAD JSON ----
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ---- PROCESS EACH OBJECT ----
    for key, value in data.items():
        folder_path = os.path.join(OUTPUT_BASE, key)
        os.makedirs(folder_path, exist_ok=True)

        links = value.get("links_found", [])

        # Write links to file
        file_path = os.path.join(folder_path, LINK_FILENAME)
        with open(file_path, "w", encoding="utf-8") as txt:
            for link in links:
                txt.write(link + "\n")

        print(f"[OK] Created {file_path} with {len(links)} links")


def visit_per_projects(folder):
    for root, dirs, files in os.walk(folder):
        for dir_name in dirs:
            folder_path = os.path.join(root, dir_name)
            print(f"Visiting folder: {folder_path}")
            grouped_data = defaultdict(list)
            try:
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file)
                    if file.endswith(".txt"):
                        with open(file_path, "r", encoding="utf-8") as f:
                            urls = [line.strip() for line in f if line.strip()]
                            print('ito',urls)
                            loader = SeleniumURLLoader(urls=urls)
                            docs = loader.load()
                            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                            documents = text_splitter.split_documents(docs)

                            for doc in documents:
                                grouped_data[dir_name].append({
                                    'text': re.sub("\n\n+", "\n", doc.page_content),
                                    'source': str(doc.metadata.get('source', 'Unknown source'))
                                })
            except FileNotFoundError:
                print("File does not exist.")
            finally:
                write_to_json(grouped_data)
