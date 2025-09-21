import os # NEW: Import the os library
import json
import httpx
from bs4 import BeautifulSoup
import datetime
from dateutil import parser
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_CALENDAR_API_KEY")


PSUB_CONFIG_URL = "https://union.purdue.edu/events/"

def _infer_psub_location(event_title, event_description=""):
    """Infer location for PSUB events based on title and description patterns."""
    if not event_title:
        return "No Location"
    
    title_lower = event_title.lower()
    description_lower = event_description.lower() if event_description else ""
    
    # Common PSUB locations and their indicators
    location_patterns = {
        'Purdue Memorial Union': ['union', 'pmu', 'memorial union'],
        'Hail Purdue Stage': ['hail purdue', 'stage', 'concert', 'performance'],
        'Purdue Memorial Union, Hail Purdue Stage': ['hail purdue stage'],
        'Purdue Memorial Union, Ever True Stage': ['ever true', 'ever true stage'],
        'Purdue Memorial Union, Front Lawn': ['front lawn', 'lawn', 'outdoor'],
        'Purdue Memorial Union, North Ballroom': ['north ballroom', 'ballroom'],
        'Purdue Memorial Union, South Ballroom': ['south ballroom', 'ballroom'],
        'Purdue Memorial Union, West Faculty Lounge': ['west faculty', 'faculty lounge'],
        'Purdue Memorial Union, Director\'s Room': ['director\'s room', 'directors room'],
        'Stadium Mall': ['stadium mall', 'stadium', 'mall'],
        'Memorial Mall': ['memorial mall', 'mall'],
        'Stewart Center': ['stewart center', 'stewart'],
        'Elliott Hall': ['elliott hall', 'elliott'],
        'Loeb Playhouse': ['loeb', 'playhouse']
    }
    
    # Check title and description for location indicators
    for location, patterns in location_patterns.items():
        for pattern in patterns:
            if pattern in title_lower or pattern in description_lower:
                return location
    
    # Default PSUB location if no specific pattern found
    return "Purdue Memorial Union"

def _get_calendar_ids():
    """Scrapes the PSUB page to find the Google Calendar IDs in the config script."""
    try:
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" }
        response = httpx.get(PSUB_CONFIG_URL, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the script tag containing the JSON configuration
        config_script = soup.find('script', id='myjson-1')
        if not config_script:
            return []
            
        config_data = json.loads(config_script.string)
        calendar_configs = config_data.get("CalendarConfiguration", [])
        
        # Extract the email/ID for each calendar
        calendar_ids = [conf['organizer']['email'] for conf in calendar_configs]
        print(f"   -> Found {len(calendar_ids)} calendar IDs to check.")
        return calendar_ids
    except Exception as e:
        print(f"   [!] Error finding calendar IDs: {e}")
        return []

def scrape_psub_events():
    """Fetches events directly from the Google Calendar API."""
    print("-> Running PSUB Scraper (Google Calendar API Method)...")
    
    if not API_KEY:
        print("   [!] GOOGLE_CALENDAR_API_KEY not found in .env file. Skipping PSUB scraper.")
        return []

    calendar_ids = _get_calendar_ids()
    if not calendar_ids:
        return []

    all_events = []
    try:
        # Build the Google Calendar service object
        service = build('calendar', 'v3', developerKey=API_KEY)
        # Get the current time in the required format
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        semester_end = datetime.datetime(2025, 12, 15, 23, 59, 59).isoformat() + 'Z'  # End of fall semester

        # Loop through each calendar ID we found (PMU, PSUB, etc.)
        for cal_id in calendar_ids:
            # Call the Calendar API with more detailed information
            events_result = service.events().list(
                calendarId=cal_id, timeMin=now, timeMax=semester_end,
                maxResults=50, singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events_from_api = events_result.get('items', [])

            for event_api in events_from_api:
                start = event_api['start'].get('dateTime', event_api['start'].get('date'))
                
                # Parse and normalize the date
                normalized_date = "unknown"
                if start:
                    try:
                        parsed_date = parser.parse(start)
                        normalized_date = parsed_date.strftime('%Y-%m-%d')
                    except parser.ParserError:
                        pass

                # Get event details
                title = event_api.get('summary', 'No Title')
                description = event_api.get('description', '')
                api_location = event_api.get('location', '')
                
                # Determine location - use API location if available, otherwise infer
                if api_location and api_location.strip():
                    location = api_location
                else:
                    location = _infer_psub_location(title, description)

                all_events.append({
                    'title': title,
                    'date_string': start,
                    'normalized_date': normalized_date,
                    'location': location,
                    'link': event_api.get('htmlLink', PSUB_CONFIG_URL),
                    'source': 'Purdue Student Union Board'
                })
        
        print(f"   -> Found {len(all_events)} events from Google Calendar API.")
        return all_events

    except Exception as e:
        print(f"   [!] An error occurred with the Google Calendar API: {e}")
        return []