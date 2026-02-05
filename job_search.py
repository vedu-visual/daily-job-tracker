import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

KEYWORDS = ["Data Analyst", "Business Analyst", "Product Analyst", "Operations Analyst"]
LOCATIONS = ["Pune", "Mumbai", "Hyderabad", "Gurugram", "Bangalore", "Remote"]

MUST_HAVE_SKILLS = ["sql", "python", "excel", "tableau"]
EXCLUDE_TITLES = ["senior", "lead", "manager", "director", "ml engineer",
                  "software", "developer", "intern", "principal"]

MAX_RESULTS = 20
HEADERS = {"User-Agent": "Mozilla/5.0"}

def score_job(title, location):
    score = 0
    title_l = title.lower()
    loc_l = location.lower()

    if "data analyst" in title_l:
        score += 5
    elif "analyst" in title_l:
        score += 3

    for loc in LOCATIONS:
        if loc.lower() in loc_l:
            score += 2

    return score


def scrape_indeed():
    jobs = []
    base_url = "https://www.indeed.com/jobs"

    for keyword in KEYWORDS:
        for location in LOCATIONS:
            params = {"q": keyword, "l": location, "fromage": 1}
            try:
                r = requests.get(base_url, params=params, headers=HEADERS, timeout=15)
                if r.status_code != 200:
                    continue
            except:
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select(".job_seen_beacon")

            for card in cards:
                title_tag = card.select_one("h2")
                company_tag = card.select_one(".companyName")
                loc_tag = card.select_one(".companyLocation")
                date_tag = card.select_one(".date")
                link_tag = card.find("a")

                if not title_tag or not company_tag or not link_tag:
                    continue

                title = title_tag.get_text(strip=True)
                company = company_tag.get_text(strip=True)
                location = loc_tag.get_text(strip=True) if loc_tag else "Unknown"
                posted = date_tag.get_text(strip=True) if date_tag else "Recent"
                link = "https://www.indeed.com" + link_tag["href"]

                if any(x in title.lower() for x in EXCLUDE_TITLES):
                    continue

                jobs.append({
                    "role": title,
                    "company": company,
                    "location": location,
                    "posted": posted,
                    "link": link
                })

    return jobs


def main():
    all_jobs = []

    print("Scraping Indeed...")
    all_jobs.extend(scrape_indeed())

    # ✅ Always create CSV even if empty
    if not all_jobs:
        df = pd.DataFrame(columns=["role", "company", "location", "posted", "link", "why_it_matches"])
        df.to_csv("results.csv", index=False)
        print("No jobs found. Empty results.csv created.")
        return

    df = pd.DataFrame(all_jobs).drop_duplicates(subset=["role", "company"])

    df["score"] = df.apply(lambda x: score_job(x["role"], x["location"]), axis=1)
    df = df[df["score"] >= 3]
    df = df.sort_values(by="score", ascending=False).head(MAX_RESULTS)

    df["why_it_matches"] = "Entry-level analyst role with location match"

    df_out = df[["role", "company", "location", "posted", "link", "why_it_matches"]]
    df_out.to_csv("results.csv", index=False)

    print("Saved results.csv with", len(df_out), "jobs")


if __name__ == "__main__":
    main()
