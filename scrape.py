#!/usr/bin/env python3
"""Daily Kenya job scraper - outputs jobs.json"""
import json, re, sys, time
from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# Stricter keywords - avoid false positives like "Operations Customer Service"
MUST_INCLUDE = [
    # Agritech/horticulture
    "trial", "variety", "agronom", "horticultur", "floricultur",
    "crop", "seed", "farm manager", "farm supervisor",
    # Data
    "data analyst", "data scientist", "business intelligence",
    "bi analyst", "analytics", "data engineer",
    # Operations (qualified)
    "operations analyst", "operations manager", "operations officer",
    "supply chain", "logistics manager",
    # Product
    "product manager", "product analyst", "product owner",
    # R&D / research
    "r&d", "research associate", "research officer", "research scientist",
    # M&E / NGO
    "monitoring and evaluation", "m&e officer", "m&e specialist",
    # Quality
    "quality assurance", "quality control", "qc analyst"
]

# Exclude these even if keyword matches
EXCLUDE = [
    "customer service", "call center", "call centre", "sales representative",
    "driver", "security guard", "cleaner", "cook", "waitress", "waiter"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def matches(text):
    t = (text or "").lower()
    if any(x in t for x in EXCLUDE):
        return False
    return any(k in t for k in MUST_INCLUDE)


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


# ============ BRIGHTERMONDAY (updated selectors) ============
def scrape_brightermonday():
    jobs = []
    base = "https://www.brightermonday.co.ke"
    try:
        for page in [1, 2, 3]:
            url = f"{base}/jobs?page={page}"
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code != 200:
                print(f"BM page {page} status {r.status_code}", file=sys.stderr)
                break
            soup = BeautifulSoup(r.text, "html.parser")

            # Try multiple selector patterns
            cards = (
                soup.select("article") or
                soup.select("div[data-testid='job-card']") or
                soup.select("a[href*='/listings/']")
            )

            found_on_page = 0
            for card in cards:
                # Get link
                if card.name == "a":
                    link = card
                else:
                    link = card.find("a", href=True)
                if not link:
                    continue

                href = link.get("href", "")
                if not href or "listings" not in href:
                    continue
                if href.startswith("/"):
                    href = base + href

                title = clean(link.get_text())
                if not title or len(title) < 5:
                    continue

                full_text = clean(card.get_text())
                if not matches(title + " " + full_text):
                    continue

                jobs.append({
                    "title": title,
                    "company": "",
                    "location": "Kenya",
                    "url": href,
                    "source": "BrighterMonday",
                    "description": full_text[:400]
                })
                found_on_page += 1

            print(f"BM page {page}: {found_on_page}", file=sys.stderr)
            if found_on_page == 0:
                break
            time.sleep(1)
    except Exception as e:
        print(f"BM error: {e}", file=sys.stderr)
    return jobs[:60]


# ============ FUZU (updated) ============
def scrape_fuzu():
    jobs = []
    base = "https://fuzu.com"
    try:
        # Fuzu search URLs
        urls = [
            f"{base}/ke_en/opportunities?q=agriculture",
            f"{base}/ke_en/opportunities?q=data+analyst",
            f"{base}/ke_en/opportunities?q=operations",
            f"{base}/ke_en/opportunities?q=research",
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=25)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")

                # Fuzu uses various card structures
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    if "/opportunities/" not in href and "/jobs/" not in href:
                        continue
                    if href.startswith("/"):
                        href = base + href

                    title = clean(link.get_text())
                    if not title or len(title) < 8 or len(title) > 150:
                        continue
                    if not matches(title):
                        continue

                    jobs.append({
                        "title": title,
                        "company": "",
                        "location": "Kenya",
                        "url": href,
                        "source": "Fuzu",
                        "description": ""
                    })
                time.sleep(1)
            except Exception as e:
                print(f"Fuzu URL error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Fuzu error: {e}", file=sys.stderr)
    return jobs[:60]


# ============ MYJOBMAG (worked before, keep + expand) ============
def scrape_myjobmag():
    jobs = []
    base = "https://www.myjobmag.co.ke"
    try:
        # Scrape main + search pages
        urls = [
            f"{base}/jobs",
            f"{base}/search?q=agriculture",
            f"{base}/search?q=data",
            f"{base}/search?q=operations",
            f"{base}/search?q=research",
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=25)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")

                for card in soup.select("li.job-list-li, li, article"):
                    link = card.find("a", href=True)
                    if not link:
                        continue
                    title = clean(link.get_text())
                    href = link.get("href", "")
                    if href.startswith("/"):
                        href = base + href
                    if not title or len(title) < 8 or "job" not in href:
                        continue
                    if not matches(title):
                        continue
                    jobs.append({
                        "title": title,
                        "company": "",
                        "location": "Kenya",
                        "url": href,
                        "source": "MyJobMag",
                        "description": clean(card.get_text())[:400]
                    })
                time.sleep(1)
            except Exception as e:
                print(f"MJM URL error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"MJM error: {e}", file=sys.stderr)
    return jobs[:60]


# ============ JOBWEBKENYA (new source) ============
def scrape_jobwebkenya():
    jobs = []
    base = "https://jobwebkenya.com"
    try:
        r = requests.get(f"{base}/", headers=HEADERS, timeout=25)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for link in soup.find_all("a", href=True):
                title = clean(link.get_text())
                href = link.get("href", "")
                if not title or len(title) < 10 or len(title) > 150:
                    continue
                if "/job/" not in href and "/vacan" not in href:
                    continue
                if not matches(title):
                    continue
                jobs.append({
                    "title": title,
                    "company": "",
                    "location": "Kenya",
                    "url": href if href.startswith("http") else base + href,
                    "source": "JobWebKenya",
                    "description": ""
                })
    except Exception as e:
        print(f"JobWebKenya error: {e}", file=sys.stderr)
    return jobs[:60]


# ============ CAREERPOINT KENYA (new source) ============
def scrape_careerpoint():
    jobs = []
    base = "https://www.careerpointkenya.co.ke"
    try:
        r = requests.get(f"{base}/category/agriculture-jobs/", headers=HEADERS, timeout=25)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for link in soup.find_all("a", href=True):
                title = clean(link.get_text())
                href = link.get("href", "")
                if not title or len(title) < 10 or len(title) > 200:
                    continue
                if not matches(title):
                    continue
                jobs.append({
                    "title": title,
                    "company": "",
                    "location": "Kenya",
                    "url": href,
                    "source": "CareerPoint",
                    "description": ""
                })
    except Exception as e:
        print(f"CareerPoint error: {e}", file=sys.stderr)
    return jobs[:60]


# ============ MAIN ============
def main():
    print("Starting scrape...")
    all_jobs = []

    for name, func in [
        ("BrighterMonday", scrape_brightermonday),
        ("Fuzu", scrape_fuzu),
        ("MyJobMag", scrape_myjobmag),
        ("JobWebKenya", scrape_jobwebkenya),
        ("CareerPoint", scrape_careerpoint),
    ]:
        try:
            result = func()
            print(f"{name}: {len(result)} jobs")
            all_jobs.extend(result)
        except Exception as e:
            print(f"{name} failed: {e}", file=sys.stderr)

    # Dedupe by title + url
    seen = set()
    unique = []
    for j in all_jobs:
        key = (j["title"].lower().strip(), j["url"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(j)

    output = {
        "updated": datetime.utcnow().isoformat() + "Z",
        "count": len(unique),
        "jobs": unique
    }
    with open("jobs.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"Saved {len(unique)} jobs")


if __name__ == "__main__":
    main()