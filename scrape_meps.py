import requests
from bs4 import BeautifulSoup
import csv
import time

# --- STEP 1: SETTING UP THE ADDRESSES ---
# This is the main page where all the committee members are listed.
BASE_URL = "https://www.europarl.europa.eu"
COMMITTEE_URL = "https://www.europarl.europa.eu/committees/en/droi/home/members"

def scrape_meps():
    print(f"Starting to fetch members from: {COMMITTEE_URL}")
    
    # --- STEP 2: GETTING THE MAIN LIST ---
    # We ask the website for the page content.
    response = requests.get(COMMITTEE_URL)
    if response.status_code != 200:
        print("Failed to load the committee page.")
        return

    # We use BeautifulSoup to "read" the HTML code of the page.
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # We look for all the links that point to MEP profiles.
    # In the current website structure, these are often inside specific 'a' tags.
    # Note: Website structures change, so we target common MEP link patterns.
    mep_links = []
    for a in soup.find_all('a', href=True):
        if '/meps/en/' in a['href'] and '/home' not in a['href']:
            # Construct the full URL without forcing '/home' suffix which can cause 404s
            full_url = a['href'] if a['href'].startswith('http') else BASE_URL + a['href']
            if full_url not in mep_links:
                mep_links.append(full_url)

    print(f"Found {len(mep_links)} potential MEP profile links.")

    # --- STEP 3: PREPARING THE EXCEL-LIKE FILE (CSV) ---
    with open('mep_data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Country", "Political Group", "National Party", "Profile URL"])

        # --- STEP 4: VISITING EACH PROFILE ---
        for link in mep_links:
            try:
                print(f"Scraping profile: {link}")
                mep_response = requests.get(link)
                mep_soup = BeautifulSoup(mep_response.text, 'html.parser')

                # --- STEP 5: EXTRACTING THE DATA ---
                # Improved selectors based on current website structure
                name_span = mep_soup.find('span', class_='sln-member-name')
                name = name_span.get_text(strip=True) if name_span else "N/A"
                
                # Country and National Party are often in a div with es_title-h3
                country_party_div = mep_soup.find('div', class_='es_title-h3')
                if country_party_div:
                    text = country_party_div.get_text(strip=True)
                    if ' - ' in text:
                        parts = text.split(' - ')
                        country = parts[0].strip()
                        national_party = parts[1].strip()
                    else:
                        country = text
                        national_party = "N/A"
                else:
                    country, national_party = "N/A", "N/A"

                # Political Group
                group_h3 = mep_soup.find('h3', class_='sln-political-group-name')
                political_group = group_h3.get_text(strip=True) if group_h3 else "N/A"

                # --- STEP 6: SAVING THE DATA ---
                writer.writerow([name, country, political_group, national_party, mep_response.url])

                # --- STEP 7: BEING POLITE ---
                # We wait 1 second between pages so we don't overwhelm the website.
                time.sleep(1)

            except Exception as e:
                print(f"Could not scrape {link} because of an error: {e}")

    print("Finished! All data has been saved to 'mep_data.csv'.")

if __name__ == "__main__":
    scrape_meps()
