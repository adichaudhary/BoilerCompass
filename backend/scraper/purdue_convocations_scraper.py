# backend/scraper/purdue_convocations_scraper.py

import httpx
import requests
from bs4 import BeautifulSoup
import datetime
from dateutil import parser
import re
import time
import random

PURDUE_CONVOCATIONS_URL = "https://convocations.purdue.edu/events/"
PURDUE_CONVOCATIONS_URLS = [
    "https://convocations.purdue.edu/events/",
    "https://convocations.purdue.edu/events/?view=list",
    "https://convocations.purdue.edu/events/?view=photo",
    "https://convocations.purdue.edu/events/?category=all"
]

def _normalize_date(date_str):
    """Normalize date string to YYYY-MM-DD format."""
    if not date_str or date_str == "No Date":
        return "unknown"
    
    try:
        # Clean up the date string - remove extra whitespace and common prefixes
        clean_date_str = date_str.strip()
        
        # Handle different date formats that might appear on the site
        # Try to parse the date directly
        parsed_date = parser.parse(clean_date_str, default=datetime.datetime.now())
        return parsed_date.strftime('%Y-%m-%d')
    except (parser.ParserError, TypeError, ValueError):
        return "unknown"

def _extract_time_from_text(text):
    """Extract time information from event text."""
    # Look for time patterns like "7:00 pm", "8:00 pm", etc.
    time_pattern = r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM))'
    match = re.search(time_pattern, text)
    return match.group(1) if match else ""

def _clean_location_text(location_text):
    """Clean up location text to extract just the venue name."""
    if not location_text or location_text == "No Location":
        return "No Location"
    
    # Remove extra whitespace and newlines
    clean_text = ' '.join(location_text.split())
    
    # Common venue names to look for
    venue_names = [
        'Elliott Hall of Music',
        'Elliott Hall',
        'Stewart Center',
        'Loeb Playhouse',
        'Memorial Union',
        'Fowler Hall',
        'Hall of Music'
    ]
    
    # Try to find a clean venue name
    for venue in venue_names:
        if venue in clean_text:
            # If the text is mostly just the venue name, return it
            if len(clean_text) < 100 and venue in clean_text:
                return venue
            # If it's a longer text, try to extract just the venue part
            venue_index = clean_text.find(venue)
            if venue_index != -1:
                # Get some context around the venue name
                start = max(0, venue_index - 20)
                end = min(len(clean_text), venue_index + len(venue) + 20)
                context = clean_text[start:end].strip()
                if len(context) < 80:  # If context is reasonable length
                    return context
    
    # If no clean venue found, return the cleaned text (truncated if too long)
    if len(clean_text) > 100:
        return clean_text[:100] + "..."
    return clean_text

def scrape_convocations_events():
    """Scrape events from Purdue Convocations website."""
    print("-> Running Purdue Convocations Scraper...")
    
    # Try multiple approaches to access the website
    approaches = [
        {
            "name": "requests Standard Chrome",
            "method": "requests",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0"
            }
        },
        {
            "name": "httpx Mac Chrome",
            "method": "httpx",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0"
            }
        },
        {
            "name": "requests Mac Chrome",
            "method": "requests",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0"
            }
        }
    ]
    
    for approach in approaches:
        for url in PURDUE_CONVOCATIONS_URLS:
            try:
                print(f"   -> Trying {approach['name']} approach with {url}...")
                
                # Add random delay to avoid rate limiting
                time.sleep(random.uniform(1, 3))
                
                if approach['method'] == 'httpx':
                    client = httpx.Client(
                        headers=approach['headers'],
                        timeout=30.0,
                        follow_redirects=True
                    )
                    response = client.get(url)
                    response.raise_for_status()
                    content = response.content
                else:  # requests
                    response = requests.get(
                        url,
                        headers=approach['headers'],
                        timeout=30.0,
                        allow_redirects=True
                    )
                    response.raise_for_status()
                    content = response.content
                
                print(f"   -> Successfully accessed website with {approach['name']} at {url}")
                soup = BeautifulSoup(content, 'html.parser')
                break
                
            except (httpx.HTTPStatusError, requests.exceptions.HTTPError) as e:
                status_code = getattr(e, 'response', None)
                if status_code:
                    status_code = status_code.status_code
                else:
                    status_code = "Unknown"
                print(f"   [!] {approach['name']} failed with HTTP {status_code} for {url}")
                continue
            except Exception as e:
                print(f"   [!] {approach['name']} failed with error: {e} for {url}")
                continue
        else:
            continue  # If no URL worked for this approach, try next approach
        break  # If we got here, we successfully accessed the website
    else:
        print("   [!] All approaches failed. Website may be blocking automated requests.")
        return []
    events_list = []
    
    # Look for event containers - based on the actual website structure
    # The convocations site has events listed in a specific format
    
    # Try multiple selectors to find event containers, being more specific
    event_containers = []
    
    # Look for events in various possible containers based on the actual site structure
    selectors_to_try = [
        'div[class*="event-item"]',  # More specific event containers
        'div[class*="event-card"]',
        'div[class*="event-listing"]',
        'article[class*="event"]',
        'li[class*="event-item"]',
        'div[class*="listing-item"]',
        'div[class*="card-item"]',
        'div.event-item',
        'div.event-card',
        'div.event-listing',
        'article.event',
        'li.event-item'
    ]
    
    for selector in selectors_to_try:
        containers = soup.select(selector)
        if containers:
            event_containers.extend(containers)
            print(f"   -> Found {len(containers)} containers with selector: {selector}")
            break
    
    # If no specific containers found, look for date patterns in the text
    if not event_containers:
        print("   [!] No event containers found with standard selectors, trying text-based parsing...")
        
        # Look for text patterns that might indicate events
        all_text = soup.get_text()
        lines = all_text.split('\n')
        
        # Look for lines that contain both a date pattern and event-like content
        for i, line in enumerate(lines):
            line = line.strip()
            if re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b', line) and len(line) > 10:
                # This might be an event line, create a mock container
                mock_container = BeautifulSoup(f'<div class="event-line">{line}</div>', 'html.parser')
                event_containers.append(mock_container.find('div'))
        
        if event_containers:
            print(f"   -> Found {len(event_containers)} events using text-based parsing")
    
    if not event_containers:
        print("   [!] Warning: No event containers found.")
        # Let's also try to debug by looking at the page structure
        print("   [!] Page title:", soup.find('title').get_text() if soup.find('title') else "No title found")
        print("   [!] Looking for any divs with 'event' in class name...")
        event_divs = soup.find_all('div', class_=lambda x: x and 'event' in x.lower())
        print(f"   [!] Found {len(event_divs)} divs with 'event' in class name")
        return []

    for event in event_containers:
        try:
            # Skip navigation elements and other non-event content
            text_content = event.get_text(strip=True).lower()
            skip_keywords = [
                'navigation', 'menu', 'search', 'filter', 'sort', 'view', 'all', 'broadway', 
                'music', 'theatre', 'dance', 'ideas', 'family', 'youth', 'student', 'free',
                'events search', 'find events', 'enter keyword', 'select date', 'today',
                'upcoming', 'previous events', 'next events', 'subscribe', 'calendar',
                'google calendar', 'icalendar', 'outlook', 'export', 'follow us',
                'facebook', 'linkedin', 'instagram', 'youtube', 'support', 'box office',
                'tickets', 'manage tickets', 'programs', 'playbills', 'know before you go',
                'give today', 'donate', 'copyright', 'accessibility', 'privacy policy'
            ]
            
            # Special case: don't skip if it contains "menopause" or "musical"
            if 'menopause' in text_content or 'musical' in text_content:
                pass  # Don't skip these
            elif any(keyword in text_content for keyword in skip_keywords):
                continue
            
            # Skip if the text is too short or looks like navigation
            if len(text_content) < 10 or text_content in ['all', 'list', 'photo', 'today', 'upcoming']:
                continue
            
            # Extract title - look for various header elements and links
            title = "No Title"
            title_element = (event.find('h1') or event.find('h2') or event.find('h3') or 
                           event.find('h4') or event.find('h5') or event.find('h6') or 
                           event.find('a') or event.find('span', class_=lambda x: x and 'title' in x.lower()))
            
            if title_element:
                title = title_element.get_text(strip=True)
            
            # If no title found in headers, try to get text content
            if title == "No Title" or len(title) < 3:
                text_content = event.get_text(strip=True)
                if text_content and len(text_content) > 5:
                    # Take the first meaningful line as title
                    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                    if lines:
                        title = lines[0]
            
            # Skip if title is still not meaningful
            if title == "No Title" or len(title) < 5 or title.lower() in skip_keywords:
                continue
            
            # Extract date information - look for various date elements
            date_str = "No Date"
            date_element = (event.find('div', class_='date') or 
                          event.find('span', class_=lambda x: x and 'date' in x.lower()) or
                          event.find('time') or
                          event.find('div', class_=lambda x: x and 'time' in x.lower()))
            
            if date_element:
                date_str = date_element.get_text(strip=True)
            else:
                # Fallback to pattern matching in text content
                text_content = event.get_text()
                
                # Look for date patterns in the text
                date_patterns = [
                    r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}',
                    r'\b\d{1,2}/\d{1,2}/\d{2,4}',
                    r'\b\d{4}-\d{2}-\d{2}',
                    r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        date_str = match.group(0)
                        break
            
            # Extract time information
            time_str = _extract_time_from_text(date_str)
            if time_str and date_str != "No Date":
                # Time is already included in date_str from our mock data
                pass
            
            # Extract location - first try to get it from the main page
            location = "No Location"
            location_element = (event.find('div', class_='location') or
                              event.find('span', class_=lambda x: x and 'location' in x.lower()) or
                              event.find('div', class_=lambda x: x and 'venue' in x.lower()) or
                              event.find('div', class_=lambda x: x and 'place' in x.lower()))
            
            if location_element:
                location = location_element.get_text(strip=True)
            else:
                # Fallback to keyword search on main page
                text_content = event.get_text()
                location_keywords = ['at ', 'in ', 'Elliott Hall', 'Stewart Center', 'Loeb Playhouse', 'Hall of Music']
                for keyword in location_keywords:
                    if keyword in text_content:
                        # Try to extract the location context
                        start_idx = text_content.find(keyword)
                        if start_idx != -1:
                            # Get some context around the keyword
                            context = text_content[max(0, start_idx-20):start_idx+50]
                            location = context.strip()
                            break
                
                # If still no location found, try to get it from the individual event page
                if location == "No Location":
                    event_link = event.find('a', href=True)
                    if event_link:
                        event_url = event_link['href']
                        try:
                            # Fetch the individual event page
                            event_headers = {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                                "Accept-Language": "en-US,en;q=0.5",
                                "Accept-Encoding": "gzip, deflate, br",
                                "DNT": "1",
                                "Connection": "keep-alive",
                                "Upgrade-Insecure-Requests": "1",
                                "Sec-Fetch-Dest": "document",
                                "Sec-Fetch-Mode": "navigate",
                                "Sec-Fetch-Site": "none",
                                "Cache-Control": "max-age=0"
                            }
                            event_response = requests.get(event_url, headers=event_headers, timeout=10.0)
                            event_response.raise_for_status()
                            event_soup = BeautifulSoup(event_response.content, 'html.parser')
                            
                            # Look for venue information on the individual page
                            event_text = event_soup.get_text()
                            venue_keywords = ['Elliott Hall', 'Stewart Center', 'Loeb Playhouse', 'Hall of Music', 'Memorial Union', 'Fowler Hall']
                            
                            for venue in venue_keywords:
                                if venue in event_text:
                                    # Find the context around the venue name
                                    lines = event_text.split('\n')
                                    for line in lines:
                                        if venue in line and len(line.strip()) > 10:
                                            # Clean up the location text
                                            clean_line = line.strip()
                                            # Remove extra whitespace and newlines
                                            clean_line = ' '.join(clean_line.split())
                                            # If it's just the venue name, use it as is
                                            if venue in clean_line and len(clean_line) < 100:
                                                location = clean_line
                                                break
                                    if location != "No Location":
                                        break
                                        
                        except Exception as e:
                            # If we can't fetch the individual page, just continue with "No Location"
                            pass
            
            # Clean up the location text
            location = _clean_location_text(location)
            
            # Extract link
            link = PURDUE_CONVOCATIONS_URL
            link_element = event.find('a', href=True)
            if link_element:
                href = link_element['href']
                if href.startswith('http'):
                    link = href
                elif href.startswith('/'):
                    link = f"https://convocations.purdue.edu{href}"
                else:
                    link = f"https://convocations.purdue.edu/{href}"
            else:
                # Create a unique link based on the event title for mock data
                title_slug = title.lower().replace(' ', '-').replace(':', '').replace(',', '')
                link = f"https://convocations.purdue.edu/events/{title_slug}"
            
            normalized_date = _normalize_date(date_str)

            events_list.append({
                'title': title,
                'date_string': date_str,
                'normalized_date': normalized_date,
                'location': location,
                'link': link,
                'source': 'Purdue Convocations'
            })
            
        except Exception as e:
            print(f"   [!] Error parsing an event: {e}")
            continue
    
    print(f"   -> Found {len(events_list)} events from Purdue Convocations.")
    return events_list
