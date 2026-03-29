import requests
from bs4 import BeautifulSoup
import csv
import time

# --- STEP 1: SETTING UP THE ADDRESSES ---
BASE_URL = "https://www.europarl.europa.eu"
COMMITTEE_URL = "https://www.europarl.europa.eu/committees/en/droi/home/members"

def scrape_meps():
    print(f"Starting to fetch members from: {COMMITTEE_URL}")
    
    response = requests.get(COMMITTEE_URL)
    if response.status_code != 200:
        print("Failed to load the committee page.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # We find all member blocks
    member_items = soup.find_all('div', class_='es_member-list-item')
    print(f"Found {len(member_items)} members on the committee page.")

    # --- STEP 2: PREPARING THE CSV FILE ---
    with open('mep_data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Country", "Political Group", "National Party", "Role", "Profile URL"])

        # --- STEP 3: PROCESSING EACH MEMBER ---
        for item in member_items:
            try:
                # Get basic info from the main committee page
                name_div = item.find('div', class_='es_title-h4')
                name = name_div.get_text(strip=True) if name_div else "N/A"
                
                link_tag = item.find('a', href=True)
                profile_link = link_tag['href'] if link_tag else ""
                if profile_link and not profile_link.startswith('http'):
                    profile_link = BASE_URL + profile_link

                # Get additional info (Role, Political Group, Country)
                info_spans = item.find_all('span', class_='sln-additional-info')
                info_texts = [span.get_text(strip=True) for span in info_spans]
                
                # Logic to identify role
                role = "Member" # Default
                for text in info_texts:
                    if "Chair" in text:
                        role = text
                        break
                
                print(f"Scraping profile for: {name} (Role: {role})")
                
                # Now visit the profile page for the rest of the data
                mep_response = requests.get(profile_link)
                mep_soup = BeautifulSoup(mep_response.text, 'html.parser')

                # Country and National Party
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

                # Save the data
                writer.writerow([name, country, political_group, national_party, role, mep_response.url])

                # Wait a bit
                time.sleep(1)

            except Exception as e:
                print(f"Could not scrape member because of an error: {e}")

    print("Finished! All data with roles has been saved to 'mep_data.csv'.")

if __name__ == "__main__":
    scrape_meps()
