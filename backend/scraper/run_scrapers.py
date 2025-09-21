# backend/scraper/run_scrapers.py

import json
import os
from .purdue_calendar_scraper import scrape_main_calendar
from .psub_scraper import scrape_psub_events
from .purdue_sports_scraper import scrape_purdue_sports
from .purdue_convocations_scraper import scrape_convocations_events
from .boilerlink_scraper import scrape_boilerlink
from .homeofpurdue_scraper import scrape_homeofpurdue_events # NEW
from .purdue_dining_scraper import scrape_purdue_dining # NEW

DATABASE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.json')

def main():
    print("Starting all scrapers...")
    
    all_events = []
    
    # Run BoilerLink scraper first
    boilerlink_events = scrape_boilerlink()
    all_events.extend(boilerlink_events)
    
    # Run the first scraper and add its events
    main_calendar_events = scrape_main_calendar()
    all_events.extend(main_calendar_events)
    
    # Run the PSUB scraper and add its events
    psub_events = scrape_psub_events()
    all_events.extend(psub_events)
    
    # Run the Purdue Sports scraper and add its events
    sports_events = scrape_purdue_sports()
    all_events.extend(sports_events)
    
    # Run the Purdue Convocations scraper and add its events
    convocations_events = scrape_convocations_events()
    all_events.extend(convocations_events)
    
    
    # NEW: Run the Home of Purdue events scraper
    homeofpurdue_events = scrape_homeofpurdue_events()
    all_events.extend(homeofpurdue_events)
    
    # NEW: Run the Purdue Dining scraper and add to combined data
    dining_menu_items = scrape_purdue_dining()
    all_events.extend(dining_menu_items)
    
    # --- Deduplication using the event link or title+date for sports ---
    print(f"-> Found {len(all_events)} raw events. Now removing duplicates...")
    
    unique_events = []
    seen_links = set()
    seen_sports = set()

    for event in all_events:
        # For sports events, use title + date as the key since they share the same link
        if event.get('source') == 'Purdue Sports':
            event_key = f"{event.get('title')}_{event.get('normalized_date')}"
            if event_key not in seen_sports:
                unique_events.append(event)
                seen_sports.add(event_key)
        # For dining events, use title + location + date as the key since they share the same link
        elif event.get('source') in ['Purdue Dining API', 'Purdue Dining (Menu Items)']:
            event_key = f"{event.get('title')}_{event.get('location')}_{event.get('normalized_date')}"
            if event_key not in seen_links:
                unique_events.append(event)
                seen_links.add(event_key)
        else:
            # For other events, use the link as before
            event_key = event.get('link')
            if event_key and event_key not in seen_links:
                unique_events.append(event)
                seen_links.add(event_key)

    # --- Write the combined, clean data to the database file ---
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_events, f, indent=2)

    print(f"All scrapers finished. Total unique items found: {len(unique_events)}.")
    print(f"Combined and deduplicated data saved to data/database.json")


if __name__ == "__main__":
    main()