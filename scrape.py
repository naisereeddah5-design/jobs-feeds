#!/usr/bin/env python3
"""Daily Kenya job scraper - outputs jobs.json"""
import json, re, sys, time
from datetime import datetime
from urllib.parse import urljoin, quote_plus
import requests
from bs4 import BeautifulSoup

MUST_INCLUDE = [
    "trial", "variety", "agronom", "horticultur", "floricultur",
    "crop", "seed", "farm manager", "farm supervisor",
    "data analyst", "data scientist", "business intelligence",
    "bi analyst", "analytics", "data engineer",
    "operations analyst", "operations manager", "operations officer",
    "supply chain", "logistics manager",
    "product manager", "product analyst", "product owner",
    "r&d", "research associate", "research officer", "research scientist",
    "monitoring and evaluation", "m&e officer", "m&e specialist",
    "quality assurance", "quality control", "qc analyst"
]

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


# ============ MYJOBMAG (working — keep as-is + pagination) ============
def scrape_myjobmag():
    jobs = []
    base = "https://www.myjobmag.co.ke"
    try:
        urls = [
            f"{base}/jobs",
            f"{base}/search?q=agriculture",
            f"{base}/search?q=data",
            f"{base}/search?q=operations",
            f"{base}/search?q=research",
            f"{base}/jobs?page=2",
            f"{base}/jobs?page=3",
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
    return jobs[:100]


# ============ BRIGHTERMONDAY (rewritten) ============
def scrape_brightermonday():
    jobs = []
    base = "https://www.brightermonday.co.ke"
    try:
        urls = [
            f"{base}/jobs",
            f"{base}/jobs?page=2",
            f"{base}/jobs?page=3",
            f"{base}/jobs/search?q=agriculture",
            f"{base}/jobs/search?q=data",
            f"{base}/jobs/search?q=research",
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=25)
                if r.status_code != 200:
                    print(f"BM {url} status {r.status_code}", file=sys.stderr)
                    continue
                soup = BeautifulSoup(r.text, "html.parser")

                # Try every possible link with /listings/ pattern
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    if "/listings/" not in href:
                        continue
                    title = clean(link.get_text())
                    if not title or len(title) < 8:
                        continue
                    if not matches(title):
                        continue
                    if not href.startswith("http"):
                        href = base + href
                    jobs.append({
                        "title": title,
                        "company": "",
                        "location": "Kenya",
                        "url": href,
                        "source": "BrighterMonday",
                        "description": ""
                    })
                time.sleep(1)
            except Exception as e:
                print(f"BM URL error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"BM error: {e}", file=sys.stderr)
    return jobs[:80]


# ============ FUZU (rewritten) ============
def scrape_fuzu():
    jobs = []
    base = "https://fuzu.com"
    try:
        urls = [
            f"{base}/ke_en/opportunities",
            f"{base}/ke_en/opportunities?q=agriculture",
            f"{base}/ke_en/opportunities?q=data",
            f"{base}/ke_en/opportunities?q=research",
            f"{base}/ke_en/opportunities?q=operations",
            f"{base}/ke_en/opportunities?q=product",
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=25)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")

                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    if "/opportunities/" not in href and "/jobs/" not in href:
                        continue
                    title = clean(link.get_text())
                    if not title or len(title) < 8 or len(title) > 200:
                        continue
                    if not matches(title):
                        continue
                    if not href.startswith("http"):
                        href = base + href
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
    return jobs[:80]


# ============ JOBWEBKENYA (rewritten) ============
def scrape_jobwebkenya():
    jobs = []
    base = "https://jobwebkenya.com"
    try:
        urls = [
            f"{base}/",
            f"{base}/category/agriculture/",
            f"{base}/category/data/",
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=25)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = link.get("href", "")
                    title = clean(link.get_text())
                    if not title or len(title) < 12 or len(title) > 200:
                        continue
                    if "job" not in href.lower() and "vacanc" not in href.lower():
                        continue
                    if not matches(title):
                        continue
                    if not href.startswith("http"):
                        href = base + href
                    jobs.append({
                        "title": title,
                        "company": "",
                        "location": "Kenya",
                        "url": href,
                        "source": "JobWebKenya",
                        "description": ""
                    })
                time.sleep(1)
            except Exception as e:
                print(f"JWK URL error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"JWK error: {e}", file=sys.stderr)
    return jobs[:80]


# ============ CAREERPOINT KENYA (rewritten) ============
def scrape_careerpoint():
    jobs = []
    base = "https://www.careerpointkenya.co.ke"
    try:
        urls = [
            f"{base}/category/agriculture-jobs/",
            f"{base}/category/data-jobs/",
            f"{base}/category/business-jobs/",
        ]
        for url in urls:
            try:
                r = requests.get(url, headers=HEADERS, timeout=25)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    title = clean(link.get_text())
                    href = link.get("href", "")
                    if not title or len(title) < 12 or len(title) > 200:
                        continue
                    if not matches(title):
                        continue
                    if not href.startswith("http"):
                        href = base + href
                    jobs.append({
                        "title": title,
                        "company": "",
                        "location": "Kenya",
                        "url": href,
                        "source": "CareerPoint",
                        "description": ""
                    })
                time.sleep(1)
            except Exception as e:
                print(f"CP URL error: {e}", file=sys.stderr)
    except Exception as e:
        print(f"CP error: {e}", file=sys.stderr)
    return jobs[:80]


# ============ KENYAN JOBS BLOG (new) ============
def scrape_kenyanjobs():
    jobs = []
    base = "https://kenyanjobs.blogspot.com"
    try:
        r = requests.get(f"{base}/search/label/Agriculture", headers=HEADERS, timeout=25)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for link in soup.find_all("a", href=True):
                title = clean(link.get_text())
                href = link.get("href", "")
                if not title or len(title) < 15 or len(title) > 200:
                    continue
                if "/20" not in href:  # blog post URLs contain year
                    continue
                if not matches(title):
                    continue
                jobs.append({
                    "title": title,
                    "company": "",
                    "location": "Kenya",
                    "url": href,
                    "source": "KenyanJobs",
                    "description": ""
                })
    except Exception as e:
        print(f"KenyanJobs error: {e}", file=sys.stderr)
    return jobs[:60]


# ============ MAIN ============
def main():
    print("Starting scrape...")
    all_jobs = []

    for name, func in [
        ("MyJobMag", scrape_myjobmag),
        ("BrighterMonday", scrape_brightermonday),
        ("Fuzu", scrape_fuzu),
        ("JobWebKenya", scrape_jobwebkenya),
        ("CareerPoint", scrape_careerpoint),
        ("KenyanJobs", scrape_kenyanjobs),
    ]:
        try:
            result = func()
            print(f"{name}: {len(result)} jobs")
            all_jobs.extend(result)
        except Exception as e:
            print(f"{name} failed: {e}", file=sys.stderr)

    # Dedupe
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