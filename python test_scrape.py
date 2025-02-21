import requests
from bs4 import BeautifulSoup
import json

WEBHOOK_URL = "https://flow.zoho.com/798732245/flow/webhook/incoming?zapikey=1001.510f2bb44ae8e95e92c15351f12bd5b5.25d612d83f478f8c8e443a03e54e0314"

BASE_URL = "https://www.jobindex.dk"
SEARCH_URL = "https://www.jobindex.dk/jobsoegning/kontor/jura"

def get_job_listings():
    response = requests.get(SEARCH_URL)
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    job_wrappers = soup.find_all("div", class_="jobsearch-result")
    
    job_list = []
    
    for job in job_wrappers:
        job_link_tag = job.find("a", href=True)
        if job_link_tag:
            job_url = BASE_URL + job_link_tag["href"] if job_link_tag["href"].startswith("/") else job_link_tag["href"]
            job_title = job_link_tag.text.strip()
            company_name_tag = job.find("div", class_="company")
            company_name = company_name_tag.text.strip() if company_name_tag else "Ukendt virksomhed"
            
            job_data = {
                "title": job_title,
                "company": company_name,
                "url": job_url
            }
            job_list.append(job_data)
    
    return job_list

def get_job_details(job):
    response = requests.get(job["url"])
    if response.status_code != 200:
        return job
    
    soup = BeautifulSoup(response.text, 'html.parser')
    contact_name = "Ukendt"
    contact_email = "Ukendt"
    
    contact_info = soup.find_all("a", href=True)
    for contact in contact_info:
        if "mailto:" in contact["href"]:
            contact_email = contact["href"].replace("mailto:", "").strip()
            contact_name = contact.text.strip() if contact.text.strip() else "Ukendt"
            break
    
    job["contact"] = {
        "first_name": contact_name.split(" ")[0] if " " in contact_name else contact_name,
        "last_name": " ".join(contact_name.split(" ")[1:]) if " " in contact_name else "",
        "email": contact_email
    }
    
    return job

def send_to_webhook(job_list):
    data = {"job_titles": job_list}
    headers = {"Content-Type": "application/json"}
    response = requests.post(WEBHOOK_URL, data=json.dumps(data), headers=headers)
    return response.status_code

job_list = get_job_listings()
detailed_jobs = [get_job_details(job) for job in job_list]

if detailed_jobs:
    status_code = send_to_webhook(detailed_jobs)
    print(f"Webhook response: {status_code}")
else:
    print("Ingen jobannoncer fundet.")
