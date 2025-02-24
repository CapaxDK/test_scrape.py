import requests
from bs4 import BeautifulSoup
import json
import time

WEBHOOK_URL = "https://flow.zoho.com/798732245/flow/webhook/incoming?zapikey=1001.510f2bb44ae8e95e92c15351f12bd5b5.25d612d83f478f8c8e443a03e54e0314"
BASE_URL = "https://www.jobindex.dk"
SEARCH_URL = "https://www.jobindex.dk/jobsoegning/kontor/jura"

def get_all_job_links():
    links = []
    page = 1
    while True:
        url = SEARCH_URL + f"?page={page}"
        response = requests.get(url)
        if response.status_code != 200:
            break
        soup = BeautifulSoup(response.text, "html.parser")
        job_wrappers = soup.find_all("div", class_="jobsearch-result")
        if not job_wrappers:
            break
        for job in job_wrappers:
            a = job.find("a", href=True)
            if a:
                job_url = a["href"] if a["href"].startswith("http") else BASE_URL + a["href"]
                links.append(job_url)
        page += 1
        time.sleep(1)
    return links

def scrape_job_details(job_url):
    response = requests.get(job_url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("h1") or soup.find("h4")
    title = title_tag.text.strip() if title_tag else "Ukendt jobtitel"
    company_tag = soup.find("div", class_="company") or soup.find("span", class_="company")
    company = company_tag.text.strip() if company_tag else "Ukendt virksomhed"
    email_tag = soup.find("a", href=lambda href: href and "mailto:" in href)
    email = email_tag["href"].replace("mailto:", "").strip() if email_tag else "Ukendt"
    contact_tag = soup.find("div", class_="job-contact-info")
    contact_name = "Ukendt"
    if contact_tag:
        name_tag = contact_tag.find("strong")
        contact_name = name_tag.text.strip() if name_tag else "Ukendt"
    first_name = contact_name.split()[0] if " " in contact_name else contact_name
    last_name = " ".join(contact_name.split()[1:]) if " " in contact_name else ""
    return {"title": title, "company": company, "contact": {"first_name": first_name, "last_name": last_name, "email": email}}

def send_to_webhook(data):
    payload = {"job_titles": data}
    headers = {"Content-Type": "application/json"}
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    return response.status_code, response.text

links = get_all_job_links()
jobs = []
for link in links:
    details = scrape_job_details(link)
    if details:
        jobs.append(details)
    time.sleep(1)
if jobs:
    status, text = send_to_webhook(jobs)
    print(status, text)
else:
    print("Ingen jobannoncer fundet")
