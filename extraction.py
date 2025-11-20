# from dotenv import load_dotenv
import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader, SeleniumURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import json
from collections import defaultdict
# from generate import process_files_with_llm
# from site_financier.yahoo import call_scheduler
import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')
# load_dotenv()
import json
import os


"""
Web scraping script for Alan Allman Associates website
https://alan-allman.com/
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import time

# ---- CONFIG ----
JSON_FILE = "alan_allman_data.json"     # <-- change with your JSON file path
OUTPUT_BASE = "aaa"         # main output folder name
LINK_FILENAME = "links_found.txt"


# folder = "dossier"
# def write_to_json(grouped_data):
#     final_data = defaultdict(lambda: defaultdict(list))

 
#     for dir_name, contents in grouped_data.items():
#         for content in contents:
#             source = content['source']
#             text = content['text']
#             final_data[dir_name][source].append(text)

#     final_output = []
#     for dir_name, sources in final_data.items():
#         dir_entry = {
#             dir_name: []
#         }
#         for source, texts in sources.items():
#             dir_entry[dir_name].append({
#                 "url": source,
#                 "content": "\n".join(texts)  
#             })
#         final_output.append(dir_entry)

#     try:

#         # if os.path.exists("data.json"):
#         #     with open("data.json", "r", encoding="utf-8") as file:
#         #         existing_data = json.load(file)
#         # else:
#         #     existing_data = []
#         if os.path.exists("data.json") and os.path.getsize("data.json") > 0:
#             try:
#                 with open("data.json", "r", encoding="utf-8") as file:
#                     existing_data = json.load(file)
#             except json.JSONDecodeError:
#                 print("⚠️ data.json est vide ou invalide, réinitialisation")
#                 existing_data = []
#         else:
#             existing_data = []


#         existing_data_dict = {list(entry.keys())[0]: entry for entry in existing_data}

#         for new_entry in final_output:
#             new_key = list(new_entry.keys())[0]
#             if new_key in existing_data_dict:

#                 existing_sources = {item["url"]: item for item in existing_data_dict[new_key][new_key]}
#                 for item in new_entry[new_key]:
#                     if item["url"] in existing_sources:

#                         existing_sources[item["url"]]["content"] = item["content"]
#                     else:

#                         existing_data_dict[new_key][new_key].append(item)
#             else:

#                 existing_data_dict[new_key] = new_entry


#         updated_data = list(existing_data_dict.values())

#         with open("data.json", "w", encoding="utf-8") as file:
#             json.dump(updated_data, file, indent=4, ensure_ascii=False)
        
#     except Exception as e:
#         print(f"Error while writing to file: {e}")

# ----------------------------------
def write_to_json(grouped_data, json_path="data1.json"):
    """
    Écrit les données regroupées dans un fichier JSON de manière sûre.
    Chaque entrée est sous la forme : {"category": "<nom>", "pages": [{"url": "...", "content": "..."}]}
    """
    final_output = []

    for category, contents in grouped_data.items():
        pages = []
        for content in contents:
            pages.append({
                "url": content.get("source", "Unknown source"),
                "content": content.get("text", "")
            })
        final_output.append({
            "category": category,
            "pages": pages
        })

    # Charger les anciennes données si possible
    existing_data = []
    if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ data.json est vide ou invalide, réinitialisation")
            existing_data = []

    # Fusionner les nouvelles données sans dupliquer les URLs
    existing_dict = {entry["category"]: entry for entry in existing_data}
    for entry in final_output:
        cat = entry["category"]
        if cat in existing_dict:
            existing_urls = {page["url"]: page for page in existing_dict[cat]["pages"]}
            for page in entry["pages"]:
                existing_urls[page["url"]] = page  # Remplace ou ajoute
            existing_dict[cat]["pages"] = list(existing_urls.values())
        else:
            existing_dict[cat] = entry

    # Écrire le JSON final
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(list(existing_dict.values()), f, indent=2, ensure_ascii=False)
    print(f"✅ Data written to {json_path}")

# --------------------------------

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
    # process_files_with_llm()
    # call_scheduler()




class AlanAllmanScraper:
    """Scraper for Alan Allman Associates website"""
    
    def __init__(self, base_url: str = "https://alan-allman.com", max_depth: int = 10):
        self.base_url = base_url.rstrip('/')
        self.max_depth = max_depth
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = {}
        self.visited_urls: Set[str] = set()
        self.domain = urlparse(base_url).netloc
        self.assigned_links: Set[str] = set()

    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a webpage and return BeautifulSoup object"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL to avoid duplicates"""
        # Remove fragment
        url = url.split('#')[0]
        # Remove trailing slash
        url = url.rstrip('/')
        return url
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be scraped"""
        parsed = urlparse(url)
        # Only follow same domain links
        if parsed.netloc and parsed.netloc != self.domain:
            return False
        # Skip common non-HTML resources
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.css', '.js', '.zip', '.doc', '.docx']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        # Skip mailto, tel, javascript links
        if url.startswith(('mailto:', 'tel:', 'javascript:', '#')):
            return False
        return True
    
    def extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract all valid links from a page"""
        links = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            # Convert relative URLs to absolute
            absolute_url = urljoin(current_url, href)
            normalized_url = self.normalize_url(absolute_url)
            
            if self.is_valid_url(normalized_url) and normalized_url not in self.visited_urls:
                links.append(normalized_url)
        
        return links
    
    def scrape_page(self, url: str, depth: int = 0) -> Dict:
        """Scrape a single page and return its data"""
        if depth > self.max_depth:
            return {}
        
        normalized_url = self.normalize_url(url)
        
        # Skip if already visited
        if normalized_url in self.visited_urls:
            return {}
        
        self.visited_urls.add(normalized_url)
        
        soup = self.fetch_page(normalized_url)
        if not soup:
            return {}
        
        # Extract page data
        page_data = {
            'url': normalized_url,
            'depth': depth,
            'scraped_at': datetime.now().isoformat(),
            'title': soup.find('title').get_text(strip=True) if soup.find('title') else '',
            'content': soup.get_text(separator=' ', strip=True),
            'links_found': [],
            'links_count': 0
        }
        
        # Extract links for further crawling
        #links = self.extract_links(soup, normalized_url)
        #page_data['links_found'] = links[:50]  # Limit to 50 links per page
        #page_data['links_count'] = len(links)
        
        # Extract links for further crawling
        links = self.extract_links(soup, normalized_url)

        # Ensure uniqueness (remove duplicates)
        # unique_links = list(set(links))

        # page_data['links_found'] = unique_links[:50]  # Limit to 50 links per page
        # page_data['links_count'] = len(unique_links)
        
        filtered_links = [link for link in links if link not in self.assigned_links]
        unique_links = list(set(filtered_links))
        # Assign them to this page
        page_data['links_found'] = unique_links[:50]
        page_data['links_count'] = len(unique_links)

        self.assigned_links.update(unique_links)
        
        # Store page data with a unique key
        page_key = normalized_url.replace(self.base_url, '').replace('/', '_') or 'homepage'
        if not page_key or page_key == '_':
            page_key = 'homepage'
        self.scraped_data[page_key] = page_data
        
        # Recursively scrape linked pages
        if depth < self.max_depth:
            print(f"  Depth {depth}: Found {len(links)} links to explore")
            for link in links[:25]:  # Limit to 20 links per page to avoid too many requests
                if link not in self.visited_urls:
                    time.sleep(0.5)  # Be respectful with requests
                    self.scrape_page(link, depth + 1)
        
        return page_data
    
    def scrape_all_pages(self) -> Dict:
        """Scrape all pages from the website with depth-based crawling"""
        print(f"Starting comprehensive scrape of Alan Allman Associates website...")
        print(f"Maximum depth: {self.max_depth}")
        print(f"Starting URL: {self.base_url}\n")
        
        # Start crawling from homepage
        self.scrape_page(self.base_url, depth=0)
        
        return self.scraped_data
    
    def save_to_json(self, filename: str = 'alan_allman_data.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to {filename}")
    
    def save_to_csv(self, filename: str = 'alan_allman_pages.csv'):
        """Save all scraped pages to CSV file"""
        if self.scraped_data:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['url', 'title', 'depth', 'links_count', 'scraped_at'])
                writer.writeheader()
                for page_data in self.scraped_data.values():
                    writer.writerow({
                        'url': page_data.get('url', ''),
                        'title': page_data.get('title', '')[:200],  # Limit title length
                        'depth': page_data.get('depth', 0),
                        'links_count': page_data.get('links_count', 0),
                        'scraped_at': page_data.get('scraped_at', '')
                    })
            print(f"Pages data saved to {filename}")
    
    def print_summary(self):
        """Print a summary of scraped data"""
        print("\n" + "="*60)
        print("SCRAPING SUMMARY")
        print("="*60)
        
        total_pages = len(self.scraped_data)
        total_links = sum(page.get('links_count', 0) for page in self.scraped_data.values())
        
        # Group pages by depth
        pages_by_depth = {}
        for page_data in self.scraped_data.values():
            depth = page_data.get('depth', 0)
            if depth not in pages_by_depth:
                pages_by_depth[depth] = 0
            pages_by_depth[depth] += 1
        
        print(f"\nTotal pages scraped: {total_pages}")
        print(f"Total unique URLs visited: {len(self.visited_urls)}")
        print(f"Total links found: {total_links}")
        print(f"\nPages by depth:")
        for depth in sorted(pages_by_depth.keys()):
            print(f"  Depth {depth}: {pages_by_depth[depth]} pages")
        
        # Show sample pages
        print(f"\nSample pages scraped:")
        for i, (key, page_data) in enumerate(list(self.scraped_data.items())[:10]):
            title = page_data.get('title', 'No title')[:50]
            depth = page_data.get('depth', 0)
            print(f"  [{depth}] {title}...")
        
        if total_pages > 10:
            print(f"  ... and {total_pages - 10} more pages")
        
        print("="*60 + "\n")




def create_category_folder():
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



def main():
    """Main function to run the scraper"""
    scraper = AlanAllmanScraper(max_depth=6)
    
    # Scrape the website
    scraper.scrape_all_pages()
    
    # Print summary
    scraper.print_summary()
    
    # Save data
    scraper.save_to_json()
    scraper.save_to_csv()
    
    print("Scraping completed successfully!")

    create_category_folder()

    print("All category created!")

    visit_per_projects('aaa')

    print("extraction finished!")
if __name__ == "__main__":
    main()





