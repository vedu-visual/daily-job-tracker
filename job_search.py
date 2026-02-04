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
DAYS_LIMIT = 1  # last 24 hours

HEADERS = {"User-Agent": "Mozilla/5.0"}

# =========================
# SCORING FUNCTION
# =========================
def score_job(title, description, location):
    score = 0
    text = (title + " " + description).lower()

    # Skill match
    for skill in MUST_HAVE_SKILLS:
        if skill in text:
            score += 3

    # Title relevance
    if "data analyst" in title.lower():
        score += 5
    elif "analyst" in title.lower():
        score += 3

    # Entry level
    if "entry" in text or "junior" in text or "0-2" in text:
        score += 4

    # Location match
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
            params = {
                "q": keyword,
                "l": location,
                "fromage": DAYS_LIMIT
            }
            r = requests.get(base_url, params=params, headers=HEADERS)
            soup = BeautifulSoup(r.text, "html.parser")

            for card in soup.select(".job_seen_beacon"):
                title = card.select_one("h2").get_text(strip=True)
                company = card.select_one(".companyName").get_text(strip=True)
                loc = card.select_one(".companyLocation").get_text(strip=True)
                link = "https://www.indeed.com" + card.find("a")["href"]
                posted = card.select_one(".date").get_text(strip=True)

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
# GREENHOUSE SEARCH (COMPANY CAREERS)
# =========================
def scrape_greenhouse():
    jobs = []
    search_url = "https://boards.greenhouse.io/embed/job_board?for="

    companies = ["deloitte", "exl", "persistent", "swiggy", "flipkart"]

    for company in companies:
        url = f"https://boards.greenhouse.io/{company}"
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        for job in soup.select("a"):
            title = job.get_text(strip=True)
            link = "https://boards.greenhouse.io" + job.get("href")

            if not any(k.lower() in title.lower() for k in ["analyst"]):
                continue

            if any(x in title.lower() for x in EXCLUDE_TITLES):
                continue

            jobs.append({
                "role": title,
                "company": company.capitalize(),
                "location": "Company site",
                "posted": "Recent (company board)",
                "link": link,
                "description": title
            })

    return jobs


# =========================
# MAIN PIPELINE
# =========================
def main():
    all_jobs = []

    print("Scraping Indeed...")
    all_jobs.extend(scrape_indeed())

    print("Scraping Greenhouse company boards...")
    all_jobs.extend(scrape_greenhouse())

    df = pd.DataFrame(all_jobs)

    # Deduplicate
    df.drop_duplicates(subset=["role", "company"], inplace=True)

    # Score jobs
    df["score"] = df.apply(lambda x: score_job(
        x["role"], x["description"], x["location"]
    ), axis=1)

    # Filter weak matches
    df = df[df["score"] >= 6]

    # Rank
    df.sort_values(by="score", ascending=False, inplace=True)

    # Limit results
    df = df.head(MAX_RESULTS)

    # Add Why it matches
    def why_match(row):
        reasons = []
        for skill in MUST_HAVE_SKILLS:
            if skill in row["description"].lower():
                reasons.append(skill.upper())
        return "Matches skills: " + ", ".join(reasons)

    df["why_it_matches"] = df.apply(why_match, axis=1)

    # Output
    df_out = df[[
        "role", "company", "location", "posted", "link", "why_it_matches"
    ]]

    df_out.to_csv("results.csv", index=False)
    print("Saved results.csv")


if __name__ == "__main__":
    main()
