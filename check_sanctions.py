import csv
import requests
import time
import os

# --- STEP 1: CONFIGURATION ---
# Function to load the API key from a hidden .env file (for security)
def load_api_key():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if 'OPENSANCTIONS_API_KEY=' in line:
                    return line.split('=')[1].strip()
    except FileNotFoundError:
        print("Error: '.env' file not found. Please create one with your API key.")
    return None

API_KEY = load_api_key()

# The web address (URL) for the OpenSanctions matching service.
API_URL = "https://api.opensanctions.org/match/default"

# We tell the API who we are using the Authorization header.
HEADERS = {
    "Authorization": f"ApiKey {API_KEY}"
} if API_KEY else {}

def screen_meps():
    if not API_KEY:
        print("Cannot start: No API key found in .env.")
        return
    print("Starting sanctions screening for MEPs...")
    
    results = []

    # --- STEP 2: READ THE MEP DATA ---
    # We open the 'mep_data.csv' file created by your previous scraper.
    try:
        with open('mep_data.csv', mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            meps = list(reader)
            print(f"Loaded {len(meps)} MEPs from mep_data.csv.")
    except FileNotFoundError:
        print("Error: 'mep_data.csv' not found. Please run the scraper first.")
        return

    # --- STEP 3: CHECK EACH MEP AGAINST THE API ---
    for mep in meps:
        name = mep['Name']
        print(f"Checking: {name}...", end=" ", flush=True)

        # We prepare the "query" - this is the information we send to the API.
        # We tell it we are looking for a 'Person' with a specific 'name'.
        query = {
            "queries": {
                "mep_query": {
                    "schema": "Person",
                    "properties": {
                        "name": [name]
                    }
                }
            }
        }

        try:
            # We send the query to the API via a POST request.
            response = requests.post(API_URL, json=query, headers=HEADERS)
            
            # If the API says "OK" (status code 200), we process the results.
            if response.status_code == 200:
                data = response.json()
                
                # The API returns a list of potential matches.
                # We look at the first match (the most likely one).
                matches = data.get('responses', {}).get('mep_query', {}).get('results', [])
                
                if matches:
                    best_match = matches[0]
                    score = best_match.get('score', 0)
                    caption = best_match.get('caption', 'N/A')
                    
                    # We consider it a "hit" if the match score is high (above 0.8).
                    if score > 0.8:
                        print(f"Found potential match! (Score: {score:.2f})")
                        mep['Sanctions Match'] = "YES"
                        mep['Match Name'] = caption
                        mep['Match Score'] = round(score, 2)
                    else:
                        print("No high-confidence matches.")
                        mep['Sanctions Match'] = "No"
                        mep['Match Name'] = "N/A"
                        mep['Match Score'] = round(score, 2)
                else:
                    print("No matches found.")
                    mep['Sanctions Match'] = "No"
                    mep['Match Name'] = "N/A"
                    mep['Match Score'] = 0
            else:
                print(f"API Error (Status {response.status_code})")
                mep['Sanctions Match'] = "Error"
                mep['Match Name'] = "N/A"
                mep['Match Score'] = 0

        except Exception as e:
            print(f"Error checking {name}: {e}")
            mep['Sanctions Match'] = "Error"
            mep['Match Name'] = "N/A"
            mep['Match Score'] = 0

        # We save the updated MEP info to our results list.
        results.append(mep)
        
        # --- STEP 4: BE POLITE ---
        # We wait a tiny bit between requests to be nice to the API servers.
        time.sleep(0.5)

    # --- STEP 5: SAVE THE RESULTS TO A NEW FILE ---
    # We create a new file so we don't overwrite your original data.
    fieldnames = ["Name", "Country", "Political Group", "National Party", "Role", "Profile URL", "Sanctions Match", "Match Name", "Match Score"]
    
    with open('mep_sanctions_results.csv', mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\nSuccess! Results saved to 'mep_sanctions_results.csv'.")

if __name__ == "__main__":
    screen_meps()
