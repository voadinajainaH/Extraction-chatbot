# main.py

from scraper.alan_scraper import AlanAllmanScraper
from scraper.post_processing import create_category_folder, visit_per_projects

def main():
    print("Scraper starting")
    scraper = AlanAllmanScraper()
    scraper.scrape_all_pages()
    print("Save all link founds")
    scraper.save_to_json()
    scraper.save_to_csv()

    create_category_folder()
    print("save to json file all data")

    visit_per_projects("aaa")

    print("Scraping & extraction completed!")

if __name__ == "__main__":
    main()
