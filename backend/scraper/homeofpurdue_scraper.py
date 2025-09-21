# backend/scraper/homeofpurdue_scraper.py

import httpx
import json
from bs4 import BeautifulSoup
import datetime
from dateutil import parser
import re

HOMEOFPURDUE_EVENTS_URL = "https://www.homeofpurdue.com/events/"

def _normalize_date(date_str):
    """Normalize date string to YYYY-MM-DD format."""
    if not date_str or date_str == "No Date":
        return "unknown"
    
    try:
        # Try to parse various date formats
        parsed_date = parser.parse(date_str)
        return parsed_date.strftime('%Y-%m-%d')
    except (parser.ParserError, TypeError, ValueError):
        return "unknown"

def _extract_date_from_text(text):
    """Extract date information from event text content."""
    if not text:
        return "No Date", "unknown"
    
    # Common date patterns
    date_patterns = [
        r'(\w+day,?\s+\w+\s+\d{1,2},?\s+\d{4})',  # "Friday, January 15, 2025"
        r'(\w+\s+\d{1,2},?\s+\d{4})',  # "January 15, 2025"
        r'(\d{1,2}/\d{1,2}/\d{4})',  # "01/15/2025"
        r'(\d{1,2}-\d{1,2}-\d{4})',  # "01-15-2025"
        r'(\w+\s+\d{1,2})',  # "January 15"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            normalized = _normalize_date(date_str)
            return date_str, normalized
    
    return "No Date", "unknown"

def _extract_location_from_text(text):
    """Extract location information from event text content."""
    if not text:
        return "No Location"
    
    # Common Lafayette-West Lafayette location patterns
    location_patterns = [
        r'at\s+([^,]+(?:Lafayette|West Lafayette|Purdue)[^,]*)',
        r'@\s+([^,]+(?:Lafayette|West Lafayette|Purdue)[^,]*)',
        r'Location:\s*([^,]+)',
        r'Where:\s*([^,]+)',
        r'Venue:\s*([^,]+)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            if location and len(location) > 3:  # Basic validation
                return location
    
    return "Lafayette-West Lafayette Area"

def _extract_events_from_json(data):
    """Extract events from JSON data structure."""
    events = []
    
    def search_for_events(obj, path=""):
        if isinstance(obj, dict):
            # Look for common event patterns in dictionaries
            if any(key in obj for key in ['title', 'name', 'eventName', 'event_title']):
                title = obj.get('title') or obj.get('name') or obj.get('eventName') or obj.get('event_title', 'No Title')
                date_str = obj.get('date') or obj.get('startDate') or obj.get('eventDate') or obj.get('dateString', 'No Date')
                location = obj.get('location') or obj.get('venue') or obj.get('place') or obj.get('address', 'No Location')
                link = obj.get('url') or obj.get('link') or obj.get('href') or HOMEOFPURDUE_EVENTS_URL
                
                date_str, normalized_date = _extract_date_from_text(str(date_str))
                if not location or location == 'No Location':
                    location = _extract_location_from_text(str(title))
                
                events.append({
                    'title': str(title),
                    'date_string': date_str,
                    'normalized_date': normalized_date,
                    'location': str(location),
                    'link': str(link),
                    'source': 'Home of Purdue (Lafayette-West Lafayette)'
                })
            
            # Recursively search nested objects
            for key, value in obj.items():
                search_for_events(value, f"{path}.{key}")
        
        elif isinstance(obj, list):
            # Search through arrays
            for i, item in enumerate(obj):
                search_for_events(item, f"{path}[{i}]")
    
    search_for_events(data)
    return events

def _extract_events_from_soup(soup):
    """Extract events from BeautifulSoup object."""
    events = []
    
    # Look for various event patterns
    event_selectors = [
        'div[class*="event"]',
        'div[class*="calendar"]',
        'div[class*="listing"]',
        'article[class*="event"]',
        'li[class*="event"]',
        '.event-item',
        '.calendar-event',
        '.event-listing'
    ]
    
    for selector in event_selectors:
        elements = soup.select(selector)
        for element in elements:
            try:
                # Extract title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'span', 'div'], class_=re.compile(r'title|name|event', re.I))
                title = title_elem.get_text(strip=True) if title_elem else element.get_text(strip=True)
                
                if not title or len(title) < 3:
                    continue
                
                # Extract description/content
                description = element.get_text(strip=True)
                
                # Extract date information
                date_str, normalized_date = _extract_date_from_text(description)
                
                # Extract location
                location = _extract_location_from_text(description)
                
                # Extract link
                link = HOMEOFPURDUE_EVENTS_URL
                link_elem = element.find('a', href=True)
                if link_elem:
                    href = link_elem['href']
                    if href.startswith('http'):
                        link = href
                    elif href.startswith('/'):
                        link = f"https://www.homeofpurdue.com{href}"
                    else:
                        link = f"https://www.homeofpurdue.com/{href}"
                
                # Filter out navigation items
                nav_keywords = ['home', 'about', 'contact', 'downtown', 'sports', 'weddings', 'meetings', 'groups', 'things to do', 'food & drink', 'places to stay', 'plan', 'media', 'partners', 'privacy', 'sitemap']
                
                if (title and len(title) > 3 and 
                    not any(nav_word in title.lower() for nav_word in nav_keywords) and
                    not title.lower() in ['events', 'things to do', 'purdue', 'food & drink', 'places to stay', 'plan']):
                    events.append({
                        'title': title,
                        'date_string': date_str,
                        'normalized_date': normalized_date,
                        'location': location,
                        'link': link,
                        'source': 'Home of Purdue (Lafayette-West Lafayette)'
                    })
                    
            except Exception as e:
                print(f"   [!] Error parsing event element: {e}")
                continue
    
    return events

def scrape_homeofpurdue_events():
    """Scrapes events from the Home of Purdue events page."""
    print("-> Running Home of Purdue Events Scraper...")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        response = httpx.get(HOMEOFPURDUE_EVENTS_URL, headers=headers, timeout=30.0)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        events_list = []
        
        # Try to find any script tags that might contain event data
        script_tags = soup.find_all('script', type='application/json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                # Look for event data in the JSON
                if isinstance(data, dict):
                    events_list.extend(_extract_events_from_json(data))
            except (json.JSONDecodeError, TypeError):
                continue
        
        # Look for iframes that might contain event calendars
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src', '')
            if any(keyword in src.lower() for keyword in ['calendar', 'event', 'booking']):
                print(f"   -> Found potential event iframe: {src}")
                # Try to fetch content from iframe
                try:
                    if src.startswith('http'):
                        iframe_response = httpx.get(src, headers=headers, timeout=15.0)
                        iframe_soup = BeautifulSoup(iframe_response.content, 'html.parser')
                        events_list.extend(_extract_events_from_soup(iframe_soup))
                except Exception as e:
                    print(f"   [!] Error fetching iframe content: {e}")
        
        # Extract events from the main page using the helper function
        events_list.extend(_extract_events_from_soup(soup))
        
        # Look for any links that might lead to individual events
        event_links = soup.find_all('a', href=True)
        for link in event_links:
            href = link['href']
            link_text = link.get_text(strip=True)
            
            # Check if this looks like an event link
            if (any(keyword in href.lower() for keyword in ['event', 'calendar', 'festival', 'concert', 'show', 'exhibition']) or
                any(keyword in link_text.lower() for keyword in ['event', 'festival', 'concert', 'show', 'exhibition', 'meeting', 'conference'])):
                
                # Skip navigation links
                nav_keywords = ['home', 'about', 'contact', 'downtown', 'sports', 'weddings', 'meetings', 'groups', 'things to do', 'food & drink', 'places to stay', 'plan']
                if not any(nav_word in link_text.lower() for nav_word in nav_keywords):
                    # Try to fetch the individual event page
                    try:
                        if href.startswith('/'):
                            full_url = f"https://www.homeofpurdue.com{href}"
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            full_url = f"https://www.homeofpurdue.com/{href}"
                        
                        event_response = httpx.get(full_url, headers=headers, timeout=10.0)
                        if event_response.status_code == 200:
                            event_soup = BeautifulSoup(event_response.content, 'html.parser')
                            event_events = _extract_events_from_soup(event_soup)
                            events_list.extend(event_events)
                    except Exception as e:
                        print(f"   [!] Error fetching event page {href}: {e}")
                        continue
        
        # Note: Alternative URLs were removed as they didn't return any events
        
        # If we still didn't find many events, try a different approach
        if len(events_list) < 5:
            print("   -> Trying alternative parsing method...")
            
            # Look for any text content that might contain event information
            page_text = soup.get_text()
            
            # Split by common event separators and look for event-like content
            potential_events = re.split(r'\n\s*\n|•|\*|-\s*', page_text)
            
            for text_block in potential_events:
                text_block = text_block.strip()
                if len(text_block) < 20:  # Skip very short text blocks
                    continue
                
                # Check if this looks like an event description
                if any(keyword in text_block.lower() for keyword in ['event', 'festival', 'concert', 'show', 'exhibition', 'meeting', 'conference', 'celebration', 'fair', 'market']):
                    # Extract title (first line or first sentence)
                    lines = text_block.split('\n')
                    title = lines[0].strip() if lines else text_block[:100]
                    
                    # Additional filtering for navigation content
                    nav_keywords = ['home', 'about', 'contact', 'downtown', 'sports', 'weddings', 'meetings', 'groups', 'things to do', 'food & drink', 'places to stay', 'plan', 'media', 'partners', 'privacy', 'sitemap']
                    
                    if (len(title) > 3 and len(title) < 200 and 
                        not any(nav_word in title.lower() for nav_word in nav_keywords) and
                        not title.lower() in ['events', 'things to do', 'purdue', 'food & drink', 'places to stay', 'plan']):
                        date_str, normalized_date = _extract_date_from_text(text_block)
                        location = _extract_location_from_text(text_block)
                        
                        events_list.append({
                            'title': title,
                            'date_string': date_str,
                            'normalized_date': normalized_date,
                            'location': location,
                            'link': HOMEOFPURDUE_EVENTS_URL,
                            'source': 'Home of Purdue (Lafayette-West Lafayette)'
                        })
        
        print(f"   -> Found {len(events_list)} events from Home of Purdue.")
        return events_list
        
    except Exception as e:
        print(f"   [!] Error fetching Home of Purdue events: {e}")
        return []

if __name__ == "__main__":
    # Test the scraper
    events = scrape_homeofpurdue_events()
    for event in events[:5]:  # Show first 5 events
        print(f"Title: {event['title']}")
        print(f"Date: {event['date_string']} ({event['normalized_date']})")
        print(f"Location: {event['location']}")
        print(f"Link: {event['link']}")
        print("-" * 50)
