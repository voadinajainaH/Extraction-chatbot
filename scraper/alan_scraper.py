# scraper/alan_scraper.py

import json
import csv
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Set


from config.settings import BASE_URL, MAX_DEPTH


class AlanAllmanScraper:

    def __init__(self, base_url=BASE_URL, max_depth=MAX_DEPTH):
        self.base_url = base_url.rstrip("/")
        self.max_depth = max_depth
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = {}
        self.visited_urls = set()
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

    def save_to_json(self, filename: str = 'data/alan_allman_data.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to {filename}")

    def save_to_csv(self, filename: str = 'data/alan_allman_pages.csv'):
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

