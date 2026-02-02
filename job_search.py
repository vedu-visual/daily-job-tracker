import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import csv

KEYWORDS = [
    "Data Analyst", "Business Analyst", "Product Analyst", "Operations Analyst"
]

LOCATIONS = [
    "Pune", "Mumbai", "Hyderabad", "Gurugram", "Bangalore", "Remote"
]

EXCLUDE = ["Senior", "Lead", "ML Engineer", "Software", "Manager", "Intern"]

QUERY_SITES = [
    "https://www.indeed.com",
    "https://www.linkedin.com/jobs"
]

results = []

for keyword in KEYWORDS:
    for location in LOCATIONS:
        url = f"https://www.indeed.com/jobs?q={keyword}&l={location}&fromage=1"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        for job in soup.select(".job_seen_beacon"):
            title = job.select_one("h2").text.strip()
            company = job.select_one(".companyName").text.strip()
            link = "https://www.indeed.com" + job.select_one("a")["href"]
            date = job.select_one(".date").text.strip()

            if any(x.lower() in title.lower() for x in EXCLUDE):
                continue

            results.append([title, company, location, date, link])

with open("results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Role", "Company", "Location", "Posted", "Link"])
    writer.writerows(results)

print("Saved results.csv")
