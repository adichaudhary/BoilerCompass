# backend/scraper/purdue_dining_scraper.py

import httpx
import json
from bs4 import BeautifulSoup
import datetime
from dateutil import parser
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

PURDUE_DINING_URL = "https://dining.purdue.edu/menus/"
PURDUE_DINING_API_BASE = "https://api.hfs.purdue.edu/Menus/v2"

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

def _extract_menu_items_from_soup(soup):
    """Extract menu items from BeautifulSoup object."""
    menu_items = []
    
    # Look for various menu patterns
    menu_selectors = [
        'div[class*="menu"]',
        'div[class*="item"]',
        'div[class*="food"]',
        'div[class*="meal"]',
        'div[class*="dining"]',
        'li[class*="menu"]',
        'li[class*="item"]',
        '.menu-item',
        '.food-item',
        '.dining-item',
        '.meal-item'
    ]
    
    for selector in menu_selectors:
        elements = soup.select(selector)
        for element in elements:
            try:
                # Extract item name/title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'span', 'div'], class_=re.compile(r'title|name|item|food', re.I))
                title = title_elem.get_text(strip=True) if title_elem else element.get_text(strip=True)
                
                if not title or len(title) < 2:
                    continue
                
                # Extract description/content
                description = element.get_text(strip=True)
                
                # Extract location/dining hall
                location = "Purdue Dining"
                location_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'location|dining|hall|restaurant', re.I))
                if location_elem:
                    location = location_elem.get_text(strip=True)
                else:
                    # Try to extract from parent elements
                    parent = element.parent
                    while parent and parent.name != 'body':
                        if parent.get('class'):
                            class_names = ' '.join(parent.get('class', []))
                            if any(keyword in class_names.lower() for keyword in ['dining', 'hall', 'restaurant', 'location']):
                                location = parent.get_text(strip=True)[:50]  # Limit length
                                break
                        parent = parent.parent
                
                # Extract meal type (breakfast, lunch, dinner, etc.)
                meal_type = "Unknown"
                meal_keywords = ['breakfast', 'lunch', 'dinner', 'brunch', 'snack', 'late night']
                for keyword in meal_keywords:
                    if keyword in description.lower() or keyword in title.lower():
                        meal_type = keyword.title()
                        break
                
                # Extract date information if available
                date_str = "No Date"
                date_patterns = [
                    r'(\w+day,?\s+\w+\s+\d{1,2},?\s+\d{4})',  # "Friday, January 15, 2025"
                    r'(\w+\s+\d{1,2},?\s+\d{4})',  # "January 15, 2025"
                    r'(\d{1,2}/\d{1,2}/\d{4})',  # "01/15/2025"
                    r'(\d{1,2}-\d{1,2}-\d{4})',  # "01-15-2025"
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        date_str = match.group(1)
                        break
                
                normalized_date = _normalize_date(date_str)
                
                # Filter out navigation items and non-food content
                nav_keywords = ['home', 'about', 'contact', 'menu', 'dining', 'hours', 'location', 'contact us', 'privacy', 'terms']
                
                if (title and len(title) > 2 and len(title) < 200 and 
                    not any(nav_word in title.lower() for nav_word in nav_keywords) and
                    not title.lower() in ['menu', 'dining', 'hours', 'location', 'contact']):
                    
                    menu_items.append({
                        'title': title,
                        'description': description[:500] if len(description) > 500 else description,  # Limit description length
                        'location': location,
                        'meal_type': meal_type,
                        'date_string': date_str,
                        'normalized_date': normalized_date,
                        'link': PURDUE_DINING_URL,
                        'source': 'Purdue Dining'
                    })
                    
            except Exception as e:
                print(f"   [!] Error parsing menu item element: {e}")
                continue
    
    return menu_items

def _extract_menu_from_json(data):
    """Extract menu items from JSON data structure."""
    menu_items = []
    
    def search_for_menu_items(obj, path=""):
        if isinstance(obj, dict):
            # Look for common menu item patterns in dictionaries
            if any(key in obj for key in ['name', 'title', 'item', 'food', 'menuItem', 'menu_item']):
                title = obj.get('name') or obj.get('title') or obj.get('item') or obj.get('food') or obj.get('menuItem') or obj.get('menu_item', 'No Title')
                description = obj.get('description') or obj.get('desc') or obj.get('details', '')
                location = obj.get('location') or obj.get('diningHall') or obj.get('restaurant') or 'Purdue Dining'
                meal_type = obj.get('mealType') or obj.get('meal') or obj.get('type', 'Unknown')
                date_str = obj.get('date') or obj.get('menuDate') or obj.get('dateString', 'No Date')
                
                normalized_date = _normalize_date(date_str)
                
                menu_items.append({
                    'title': str(title),
                    'description': str(description),
                    'location': str(location),
                    'meal_type': str(meal_type),
                    'date_string': date_str,
                    'normalized_date': normalized_date,
                    'link': PURDUE_DINING_URL,
                    'source': 'Purdue Dining'
                })
            
            # Recursively search nested objects
            for key, value in obj.items():
                search_for_menu_items(value, f"{path}.{key}")
        
        elif isinstance(obj, list):
            # Search through arrays
            for i, item in enumerate(obj):
                search_for_menu_items(item, f"{path}[{i}]")
    
    search_for_menu_items(data)
    return menu_items

def _scrape_from_api():
    """Scrape menu items from the Purdue Dining API."""
    print("   -> Using Purdue Dining API...")
    
    menu_items = []
    
    try:
        # Get all locations first
        locations_url = f"{PURDUE_DINING_API_BASE}/locations"
        response = httpx.get(locations_url, timeout=10.0)
        
        if response.status_code != 200:
            print(f"   [!] Error fetching locations: {response.status_code}")
            return []
        
        locations_data = response.json()
        
        # The API returns an object with a Location array
        locations = locations_data.get('Location', []) if isinstance(locations_data, dict) else locations_data
        
        # Extract menu information from locations data
        for location in locations:
            location_name = location.get('Name', 'Unknown Location')
            location_id = location.get('LocationId', '')
            location_type = location.get('Type', 'Unknown')
            
            # Get upcoming meals for this location
            upcoming_meals = location.get('UpcomingMeals', [])
            
            for meal in upcoming_meals:
                meal_id = meal.get('ID', '')
                meal_name = meal.get('Name', 'Unknown Meal')
                meal_type = meal.get('Type', 'Unknown')
                start_time = meal.get('StartTime', '')
                end_time = meal.get('EndTime', '')
                
                # Parse the date from start_time
                try:
                    if start_time:
                        from dateutil import parser
                        start_datetime = parser.parse(start_time)
                        date_string = start_datetime.strftime("%B %d, %Y")
                        normalized_date = start_datetime.strftime("%Y-%m-%d")
                    else:
                        date_string = "Unknown Date"
                        normalized_date = "unknown"
                except:
                    date_string = "Unknown Date"
                    normalized_date = "unknown"
                
                # Create menu items based on the meal information
                # Since we don't have actual menu items, we'll create entries for the meal times
                menu_items.append({
                    'title': f"{meal_name} at {location_name}",
                    'description': f"{meal_type} service at {location_name}. Hours: {start_time} - {end_time}",
                    'location': location_name,
                    'meal_type': meal_type,
                    'meal_id': meal_id,
                    'date_string': date_string,
                    'normalized_date': normalized_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'link': PURDUE_DINING_URL,
                    'source': 'Purdue Dining API'
                })
        
        # Try to get actual menu items if possible
        # Let's try some common API patterns
        menu_endpoints = [
            f"{PURDUE_DINING_API_BASE}/menu",
            f"{PURDUE_DINING_API_BASE}/menus",
            f"{PURDUE_DINING_API_BASE}/items",
            f"{PURDUE_DINING_API_BASE}/food"
        ]
        
        for endpoint in menu_endpoints:
            try:
                response = httpx.get(endpoint, timeout=5.0)
                if response.status_code == 200:
                    print(f"   -> Found additional data at {endpoint}")
                    # Try to parse as JSON
                    try:
                        data = response.json()
                        # Extract menu items from this data
                        additional_items = _extract_menu_from_json(data)
                        menu_items.extend(additional_items)
                    except:
                        # If not JSON, try to parse as HTML/XML
                        soup = BeautifulSoup(response.content, 'html.parser')
                        additional_items = _extract_menu_items_from_soup(soup)
                        menu_items.extend(additional_items)
            except:
                continue
        
    except Exception as e:
        print(f"   [!] Error with API request: {e}")
        return []
    
    return menu_items

def _scrape_with_selenium():
    """Scrape menu items using Selenium to handle JavaScript rendering."""
    print("   -> Using Selenium to handle JavaScript...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(PURDUE_DINING_URL)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 20)
        
        # Wait for any content to load (look for common menu-related elements)
        try:
            # Wait for any element that might contain menu data
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(5)  # Additional wait for JavaScript to load
            
            # Get the page source after JavaScript execution
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract menu items from the rendered content
            menu_items = _extract_menu_items_from_soup(soup)
            
            # Also try to find any JSON data in script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and ('menu' in script.string.lower() or 'dining' in script.string.lower()):
                    try:
                        # Try to extract JSON data
                        json_match = re.search(r'\{.*\}', script.string, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group())
                            menu_items.extend(_extract_menu_from_json(data))
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            return menu_items
            
        except TimeoutException:
            print("   [!] Timeout waiting for page to load")
            return []
            
    except Exception as e:
        print(f"   [!] Error with Selenium: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def scrape_purdue_dining():
    """Scrapes menu items from the Purdue dining menus page."""
    print("-> Running Purdue Dining Scraper...")
    
    # First try the API approach for basic meal info
    try:
        basic_menu_items = _scrape_from_api()
        print(f"   -> Found {len(basic_menu_items)} basic menu items from API.")
    except Exception as e:
        print(f"   [!] Error with API request: {e}")
        basic_menu_items = []
    
    # Now get detailed menu items with dietary tags
    try:
        from .menu_items_scraper import scrape_detailed_menu_items
        detailed_items = scrape_detailed_menu_items()
        print(f"   -> Found {len(detailed_items)} detailed menu items with dietary tags.")
    except Exception as e:
        print(f"   [!] Error getting detailed menu items: {e}")
        detailed_items = []
    
    # Combine both types of data
    all_items = basic_menu_items + detailed_items
    
    print(f"   -> Total menu items found: {len(all_items)}")
    return all_items

if __name__ == "__main__":
    # Test the scraper
    menu_items = scrape_purdue_dining()
    for item in menu_items[:5]:  # Show first 5 items
        print(f"Title: {item['title']}")
        print(f"Description: {item['description'][:100]}...")
        print(f"Location: {item['location']}")
        print(f"Meal Type: {item['meal_type']}")
        print(f"Date: {item['date_string']} ({item['normalized_date']})")
        print("-" * 50)
