# backend/scraper/boilerlink_scraper.py (Final Version)

import httpx
import datetime
from dateutil import parser

# This is the API URL you found, modified to get up to 200 upcoming events.
BOILERLINK_API_URL = "https://boilerlink.purdue.edu/api/discovery/event/search?endsAfter=2025-09-20T00:00:00-04:00&orderByField=endsOn&orderByDirection=ascending&status=Approved&take=200&query="

def _normalize_date(date_str):
    if not date_str: return "unknown"
    try:
        parsed_date = parser.parse(date_str)
        return parsed_date.strftime('%Y-%m-%d')
    except (parser.ParserError, TypeError):
        return "unknown"

def scrape_boilerlink():
    """Scrapes the BoilerLink platform by hitting its internal API."""
    print("-> Running BoilerLink Scraper...")
    try:
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" }
        response = httpx.get(BOILERLINK_API_URL, headers=headers, timeout=30.0)
        response.raise_for_status()
        json_data = response.json()
    except Exception as e:
        print(f"   [!] Error fetching BoilerLink API: {e}")
        return []

    events_list = []
    
    # This type of API often nests the list of results inside a 'value' key.
    # Check the "Preview" tab in your browser's dev tools to confirm.
    for event in json_data.get('value', []):
        try:
            # These are the most common keys for this platform.
            # Double-check them against the JSON preview in your browser.
            title = event.get('name', "No Title")
            date_str = event.get('startsOn', "No Date")
            location = event.get('location', "No Location")
            event_id = event.get('id')
            link = f"https://boilerlink.purdue.edu/event/{event_id}" if event_id else "#"

            normalized_date = _normalize_date(date_str)

            events_list.append({
                'title': title,
                'date_string': date_str,
                'normalized_date': normalized_date,
                'location': location,
                'link': link,
                'source': 'BoilerLink (Student Orgs)'
            })
        except Exception as e:
            print(f"   [!] Error parsing a BoilerLink event from JSON: {e}")
            continue
    
    print(f"   -> Found {len(events_list)} events from BoilerLink.")
    return events_list