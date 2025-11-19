# scraper/alan_scraper.py

import json
import csv
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

from config.settings import BASE_URL, MAX_DEPTH


class AlanAllmanScraper:

    def __init__(self, base_url=BASE_URL, max_depth=MAX_DEPTH):
        self.base_url = base_url.rstrip("/")
        self.max_depth = max_depth
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0"
        })
        self.scraped_data = {}
        self.visited_urls = set()
        self.domain = urlparse(base_url).netloc
        self.assigned_links = set()

    def fetch_page(self, url):
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return BeautifulSoup(resp.content, "html.parser")
        except:
            return None

    def normalize_url(self, url):
        return url.split("#")[0].rstrip("/")

    def is_valid_url(self, url):
        parsed = urlparse(url)

        if parsed.netloc and parsed.netloc != self.domain:
            return False

        skip = [".pdf", ".jpg", ".png", ".css", ".js", ".zip", ".doc", ".docx"]
        if any(url.lower().endswith(ext) for ext in skip):
            return False

        if url.startswith(("mailto:", "tel:", "javascript:")):
            return False

        return True

    def extract_links(self, soup, current_url):
        links = []
        for a in soup.find_all("a", href=True):
            url = self.normalize_url(urljoin(current_url, a["href"]))
            if self.is_valid_url(url) and url not in self.visited_urls:
                links.append(url)
        return links

    def scrape_page(self, url, depth=0):
        if depth > self.max_depth:
            return {}

        url = self.normalize_url(url)
        if url in self.visited_urls:
            return {}

        self.visited_urls.add(url)

        soup = self.fetch_page(url)
        if not soup:
            return {}

        links = self.extract_links(soup, url)
        unique_links = list(set([l for l in links if l not in self.assigned_links]))

        self.assigned_links.update(unique_links)

        page_data = {
            "url": url,
            "depth": depth,
            "scraped_at": datetime.now().isoformat(),
            "title": soup.find("title").get_text(strip=True) if soup.find("title") else "",
            "content": soup.get_text(" ", strip=True),
            "links_found": unique_links[:50],
            "links_count": len(unique_links)
        }

        key = url.replace(self.base_url, "").replace("/", "_").lstrip("_") or "homepage"
        self.scraped_data[key] = page_data

        if depth < self.max_depth:
            for link in links[:25]:
                time.sleep(0.5)
                self.scrape_page(link, depth + 1)

        return page_data

    def scrape_all_pages(self):
        self.scrape_page(self.base_url, depth=0)
        return self.scraped_data

    def save_to_json(self, filename="data/alan_allman_data.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)

    def save_to_csv(self, filename="data/alan_allman_pages.csv"):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["url", "title", "depth", "links_count", "scraped_at"])
            writer.writeheader()
            for p in self.scraped_data.values():
                writer.writerow({
                    "url": p["url"],
                    "title": p["title"][:200],
                    "depth": p["depth"],
                    "links_count": p["links_count"],
                    "scraped_at": p["scraped_at"]
                })
