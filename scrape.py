#!/usr/bin/env python3
"""Daily Kenya job scraper - outputs jobs.json"""
import json, re, sys, time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

KEYWORDS = [
    "trial", "variety", "agronom", "crop", "horticultur", "flori",
    "r&d", "research", "data analyst", "operations", "product",
    "quality", "supply chain", "m&e", "monitoring", "evaluation",
    "agritech", "agricultur"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def matches(text):
    t = (text or "").lower()
    return any(k in t for k in KEYWORDS)

def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()

def scrape_brightermonday():
    jobs = []
    base = "https://www.brightermonday.co.ke"
    try:
        for page in [1, 2]:
            r = requests.get(f"{base}/jobs?page={page}", headers=HEADERS, timeout=20)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("article, div.job-card, div[class*='job']"):
                link = card.find("a", href=True)
                if not link: continue
                title = clean(link.get_text())
                href = link["href"]
                if href.startswith("/"): href = base + href
                if not title or "job" not in href: continue
                if not matches(title + " " + card.get_text()): continue
                jobs.append({
                    "title": title, "company": "",
                    "location": "Kenya", "url": href,
                    "source": "BrighterMonday",
                    "description": clean(card.get_text())[:400]
                })
            time.sleep(1)
    except Exception as e:
        print(f"BM error: {e}", file=sys.stderr)
    return jobs[:40]

def scrape_fuzu():
    jobs = []
    base = "https://fuzu.com"
    try:
        r = requests.get(f"{base}/ke_en/opportunities?q=agri", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("a[href*='/opportunities/']"):
                title = clean(card.get_text())
                href = card["href"]
                if href.startswith("/"): href = base + href
                if not title or len(title) < 5: continue
                if not matches(title): continue
                jobs.append({
                    "title": title, "company": "",
                    "location": "Kenya", "url": href,
                    "source": "Fuzu", "description": ""
                })
    except Exception as e:
        print(f"Fuzu error: {e}", file=sys.stderr)
    return jobs[:40]

def scrape_myjobmag():
    jobs = []
    base = "https://www.myjobmag.co.ke"
    try:
        r = requests.get(f"{base}/jobs", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.select("li.job-list-li, div.job-list-item, li"):
                link = card.find("a", href=True)
                if not link: continue
                title = clean(link.get_text())
                href = link["href"]
                if href.startswith("/"): href = base + href
                if not title or len(title) < 5 or "job" not in href: continue
                if not matches(title): continue
                jobs.append({
                    "title": title, "company": "",
                    "location": "Kenya", "url": href,
                    "source": "MyJobMag",
                    "description": clean(card.get_text())[:400]
                })
    except Exception as e:
        print(f"MJM error: {e}", file=sys.stderr)
    return jobs[:40]

def main():
    all_jobs = []
    all_jobs.extend(scrape_brightermonday())
    print(f"BM: {len(all_jobs)}")
    all_jobs.extend(scrape_fuzu())
    print(f"+Fuzu: {len(all_jobs)}")
    all_jobs.extend(scrape_myjobmag())
    print(f"+MJM: {len(all_jobs)}")
    
    seen = set()
    unique = []
    for j in all_jobs:
        key = (j["title"].lower(), j["url"])
        if key in seen: continue
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