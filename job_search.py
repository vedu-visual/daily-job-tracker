import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import re

# =========================
# CONFIG
# =========================
KEYWORDS = [
    "Data Analyst", "Business Analyst", "Product Analyst", "Operations Analyst"
]

LOCATIONS = ["Pune", "Mumbai", "Hyderabad", "Gurugram", "Bangalore", "Remote"]

MUST_HAVE_SKILLS = ["sql", "python", "excel", "tableau"]

EXCLUDE_TITLES = [
    "senior", "lead", "manager", "director", "ml engineer",
    "software", "developer", "intern", "principal"
]

MAX_RESULTS = 20
DAYS_LIMIT = 1
HEADERS = {"User-Agent": "Mozilla/5.0"}

# =========================
# SCORING
# =========================
def score_job(title, description, location):
    score = 0
    text = (title + " " + description).lower()

    for skill in MUST_HAVE_SKILLS:
        if skill in text:
            score += 3

    if "data analyst" in title.lower():
        score += 5
    elif "analyst" in title.lower():
        score += 3

    if "entry" in text or "junior" in text or "0-2" in text:
        score += 4

    for loc in LOCATIONS:
        if loc.lower() in location.lower():
            score += 2

    return score

# =========================
# INDEED SCRAPER
# =========================
def scrape_indeed():
    jobs = []
    base_url = "https://www.indeed.com/jobs"

    for keyword in KEYWORDS:
        for location in LOCATIONS:
            params = {"q": keyword, "l": location, "fromage": DAYS_LIMIT}
            r = requests.get(base_url, params=params, headers=HEADERS, timeout=15)

            if r.status_code != 200:
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            for card in soup.select(".job_seen_beacon"):
                title = card.select_one("h2")
                company = card.select_one(".companyName")
                loc = card.select_one(".companyLocation")
                date = card.select_one(".date")
                link_tag = card.find("a")

                if not title or not company or not link_tag:
                    continue

                title = title.get_text(strip=True)
                company = company.get_text(strip=True)
                loc = loc.get_text(strip=True) if loc else ""
                posted = date.get_text(strip=True) if date else "Recent"
                link = "https://www.indeed.com" + link_tag["href"]

                if any(x in title.lower() for x in EXCLUDE_TITLES):
                    continue

                jobs.append({
                    "role": title,
                    "company": company,
                    "location": loc,
                    "posted": posted,
                    "link": link,
                    "description": title
                })

    return jobs

# =========================
# GREENHOUSE
# =========================
def scrape_greenhouse():
    jobs = []
    companies = ["deloitte", "exl", "persistent", "swiggy", "flipkart"]

    for company in companies:
        url = f"https://boards.greenhouse.io/{company}"
        r = requests.get(url, headers=HEADERS, timeout=15)

        if r.status_code != 200:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        for job in soup.select("a"):
            title = job.get_text(strip=True)
            link = job.get("href")

            if not link:
                continue

            if not any(k in title.lower() for k in ["analyst"]):
                continue

            if any(x in title.lower() for x in EXCLUDE_TITLES):
                continue

            jobs.append({
                "role": title,
                "company": company.capitalize(),
                "location": "Company site",
                "posted": "Recent (company board)",
                "link": "https://boards.greenhouse.io" + link,
                "description": title
            })

    return jobs

# =========================
# MAIN
# =========================
def main():
    all_jobs = []

    print("Scraping Indeed...")
    all_jobs.extend(scrape_indeed())

    print("Scraping Greenhouse company boards...")
    all_jobs.extend(scrape_greenhouse())

    # ✅ SAFETY: if nothing found
    if not all_jobs:
        print("No jobs found. Writing empty CSV.")
        pd.DataFrame(columns=["role","company","location","posted","link","why_it_matches"]).to_csv("results.csv", index=False)
        return

    df = pd.DataFrame(all_jobs)

    df.drop_duplicates(subset=["role", "company"], inplace=True)

    df["score"] = df.apply(lambda x: score_job(
        x["role"], x["description"], x["location"]
    ), axis=1)

    df = df[df["score"] >= 6]
    df.sort_values(by="score", ascending=False, inplace=True)
    df = df.head(MAX_RESULTS)

    def why_match(row):
        skills = [s.upper() for s in MUST_HAVE_SKILLS if s in row["description"].lower()]
        return "Matches skills: " + ", ".join(skills)

    df["why_it_matches"] = df.apply(why_match, axis=1)

    df_out = df[["role","company","location","posted","link","why_it_matches"]]

    df_out.to_csv("results.csv", index=False)
    print("Saved results.csv")

if __name__ == "__main__":
    main()
