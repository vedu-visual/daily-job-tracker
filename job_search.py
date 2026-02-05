import requests
from bs4 import BeautifulSoup
import pandas as pd

KEYWORDS = ["analyst"]
LOCATIONS = ["pune", "mumbai", "hyderabad", "gurugram", "bangalore", "remote"]

EXCLUDE_TITLES = ["senior", "lead", "manager", "director", "ml engineer",
                  "software", "developer", "principal"]

MAX_RESULTS = 20
HEADERS = {"User-Agent": "Mozilla/5.0"}

GREENHOUSE_COMPANIES = [
    "deloitte", "exl", "persistent", "swiggy", "flipkart", "razorpay"
]

LEVER_COMPANIES = [
    "swiggy", "razorpay", "cred", "groww"
]

def is_valid(title):
    t = title.lower()
    if not any(k in t for k in KEYWORDS):
        return False
    if any(x in t for x in EXCLUDE_TITLES):
        return False
    return True

def scrape_greenhouse():
    jobs = []
    for company in GREENHOUSE_COMPANIES:
        url = f"https://boards.greenhouse.io/{company}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
        except:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.select("a"):
            title = a.get_text(strip=True)
            link = a.get("href")

            if not link or not title:
                continue

            if not is_valid(title):
                continue

            jobs.append({
                "role": title,
                "company": company.capitalize(),
                "location": "Company careers",
                "posted": "Recent (company board)",
                "link": "https://boards.greenhouse.io" + link,
                "why_it_matches": "Direct company posting for analyst role"
            })
    return jobs

def scrape_lever():
    jobs = []
    for company in LEVER_COMPANIES:
        url = f"https://jobs.lever.co/{company}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
        except:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.select("a.posting-title"):
            title = a.get_text(strip=True)
            link = a.get("href")

            if not is_valid(title):
                continue

            jobs.append({
                "role": title,
                "company": company.capitalize(),
                "location": "Company careers",
                "posted": "Recent (company board)",
                "link": link,
                "why_it_matches": "Direct company posting for analyst role"
            })
    return jobs

def main():
    all_jobs = []

    print("Scraping Greenhouse boards...")
    all_jobs.extend(scrape_greenhouse())

    print("Scraping Lever boards...")
    all_jobs.extend(scrape_lever())

    df = pd.DataFrame(all_jobs).drop_duplicates(subset=["role","company"])

    if df.empty:
        df = pd.DataFrame(columns=["role","company","location","posted","link","why_it_matches"])
        df.to_csv("results.csv", index=False)
        print("No jobs found.")
        return

    df = df.head(MAX_RESULTS)
    df.to_csv("results.csv", index=False)
    print("Saved results.csv with", len(df), "jobs")

if __name__ == "__main__":
    main()
