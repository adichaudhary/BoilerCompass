# backend/scraper/purdue_calendar_scraper.py (Final Version)

import httpx
from bs4 import BeautifulSoup
import datetime
from dateutil import parser

# We'll scrape the main page, as it contains the featured events and others.
PURDUE_URL = "https://events.purdue.edu/"

def _normalize_date(date_str):
    if not date_str or date_str == "No Date": return "unknown"
    try:
        clean_date_str = date_str.split(' to ')[0].strip()
        parsed_date = parser.parse(clean_date_str, default=datetime.datetime.now())
        return parsed_date.strftime('%Y-%m-%d')
    except (parser.ParserError, TypeError):
        return "unknown"

def scrape_main_calendar():
    print("-> Running Purdue Calendar Scraper...")
    try:
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" }
        response = httpx.get(PURDUE_URL, headers=headers, timeout=20.0)
        response.raise_for_status()
    except Exception as e:
        print(f"   [!] Error fetching URL {PURDUE_URL!r}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    events_list = []
    # This selector should find all event cards, featured or not
    event_containers = soup.select('div.em-card')

    if not event_containers:
        print("   [!] Warning: No event containers found.")

    for event in event_containers:
        try:
            title_element = event.select_one('h3.em-card_title a')
            date_element = event.select_one('em-local-time')
            
            title = title_element.get_text(strip=True) if title_element else "No Title"
            date_str = date_element.get_text(strip=True) if date_element else "No Date"
            link = title_element['href'] if title_element and title_element.has_attr('href') else "#"
            
            # --- FINAL, ROBUST LOCATION FINDING LOGIC ---
            location = "No Location"
            # 1. Try to find the "featured event" location structure first
            location_element = event.select_one('p.em-text_icon a i.fa-map-marker-alt')
            if location_element:
                location = location_element.parent.get_text(strip=True)
            else:
                # 2. If that fails, try to find the "list event" structure
                location_element = event.select_one('p.em-card_event-text i.fas')
                if location_element:
                    location = location_element.parent.get_text(strip=True)
            # --- End of Location Logic ---
            
            normalized_date = _normalize_date(date_str)

            events_list.append({
                'title': title,
                'date_string': date_str,
                'normalized_date': normalized_date,
                'location': location,
                'link': link,
                'source': 'Purdue Calendar'
            })
        except Exception as e:
            print(f"   [!] Error parsing an event card: {e}")
            continue
    
    print(f"   -> Found {len(events_list)} events from Purdue Calendar.")
    return events_list