
import requests
import json
import csv
import time
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict

BASE = "https://books.toscrape.com"

STAR_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


# ── Data model ─────────────────────────────────────────────────────────────────
@dataclass
class Book:
    title:        str
    rating:       int        
    price:        str
    category:     str
    availability: str
    reviews:      int
    url:          str

    def show(self):
        stars = "★" * self.rating + "☆" * (5 - self.rating)
        print(f"  {stars}  {self.title}")
        print(f"         Price: {self.price}  |  Category: {self.category}  |  Availability: {self.availability}  |  Reviews: {self.reviews}")
        print()


# ── Helpers ────────────────────────────────────────────────────────────────────
def get(url):
    time.sleep(0.4)
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def scrape_detail(url):
    """Fetch category and review count from a book's detail page."""
    try:
        soup      = get(url)
        crumbs    = soup.select("ul.breadcrumb li")
        category  = crumbs[-2].get_text(strip=True) if len(crumbs) >= 2 else "Unknown"
        rev_el    = soup.select_one("table.table-striped tr:last-child td")
        reviews   = int(rev_el.get_text(strip=True)) if rev_el else 0
        return category, reviews
    except Exception:
        return "Unknown", 0


def scrape_page(url):
    """Scrape one listing page, return list of Books + next page URL."""
    soup  = get(url)
    books = []

    for article in soup.select("article.product_pod"):
        title_el  = article.select_one("h3 a")
        title     = title_el["title"] if title_el else "Unknown"

        star_el   = article.select_one("p.star-rating")
        word      = star_el["class"][1] if star_el else "Zero"
        rating    = STAR_MAP.get(word, 0)

        price_el  = article.select_one("p.price_color")
        price     = price_el.get_text(strip=True) if price_el else "N/A"

        avail_el  = article.select_one("p.availability")
        avail     = avail_el.get_text(strip=True) if avail_el else "Unknown"

        href      = title_el["href"].replace("../", "") if title_el else ""
        detail    = f"{BASE}/catalogue/{href}"

        category, reviews = scrape_detail(detail)

        books.append(Book(title, rating, price, category, avail, reviews, detail))

    next_btn  = soup.select_one("li.next a")
    next_url  = None
    if next_btn:
        href     = next_btn["href"]
        next_url = f"{BASE}/catalogue/{href}" if "catalogue" not in href else f"{BASE}/{href}"

    return books, next_url


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Real-Time Scraper  ->  books.toscrape.com")
    print("  Fields: title, rating, price, category,")
    print("          availability, review count, url")
    print("=" * 55)

    try:
        max_pages = int(input("\n  Pages to scrape? (1 page = 20 books): ").strip())
    except ValueError:
        max_pages = 2

    print()
    all_books = []
    url       = f"{BASE}/catalogue/page-1.html"
    page      = 1

    while url and page <= max_pages:
        print(f"  --- Page {page} ---")
        books, url = scrape_page(url)
        all_books.extend(books)
        for b in books:
            b.show()
        page += 1

    if not all_books:
        print("  No data scraped.")
        return

    with open("reviews.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=asdict(all_books[0]).keys())
        w.writeheader()
        w.writerows([asdict(b) for b in all_books])

    with open("reviews.json", "w", encoding="utf-8") as f:
        json.dump([asdict(b) for b in all_books], f, indent=2)

    avg = sum(b.rating for b in all_books) / len(all_books)
    print("=" * 55)
    print(f"  Done!  {len(all_books)} books scraped")
    print(f"  Avg rating : {avg:.2f} / 5")
    print(f"  Saved to   : reviews.csv  and  reviews.json")
    print("=" * 55)


if __name__ == "__main__":
    main()