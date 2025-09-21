# backend/scraper/detailed_menu_scraper.py

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
        parsed_date = parser.parse(date_str)
        return parsed_date.strftime('%Y-%m-%d')
    except (parser.ParserError, TypeError, ValueError):
        return "unknown"

def _scrape_detailed_menus_with_selenium():
    """Scrape detailed menu items using Selenium to interact with the React app."""
    print("   -> Using Selenium to scrape detailed menu items...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    driver = None
    menu_items = []
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(PURDUE_DINING_URL)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 20)
        time.sleep(10)  # Wait for React to load
        
        print(f"   -> Page loaded: {driver.title}")
        
        # Look for any clickable elements that might show menu details
        clickable_elements = driver.find_elements(By.CSS_SELECTOR, "a, button, [role='button'], [onclick]")
        print(f"   -> Found {len(clickable_elements)} clickable elements")
        
        # Try to find and click on dining court links
        dining_court_links = []
        for elem in clickable_elements:
            try:
                text = elem.text.strip().lower()
                if any(court in text for court in ['earhart', 'wiley', 'windsor', 'ford', 'hillenbrand', '1bowl', 'sushi']):
                    href = elem.get_attribute('href')
                    if href and 'dining' in href.lower():
                        dining_court_links.append((elem, href))
                        print(f"   -> Found dining court link: {text} -> {href}")
            except:
                continue
        
        # Try clicking on dining court links to get detailed menus
        for elem, href in dining_court_links[:3]:  # Try first 3
            try:
                print(f"   -> Clicking on: {elem.text}")
                driver.execute_script("arguments[0].click();", elem)
                time.sleep(3)
                
                # Look for menu items on the new page
                menu_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='menu'], [class*='item'], [class*='food'], [class*='card']")
                print(f"   -> Found {len(menu_elements)} potential menu elements")
                
                for menu_elem in menu_elements[:10]:  # Check first 10
                    try:
                        text = menu_elem.text.strip()
                        if text and len(text) > 5 and len(text) < 200:
                            # Look for dietary tags
                            tags = menu_elem.find_elements(By.CSS_SELECTOR, "[class*='tag'], [class*='badge'], [class*='label'], [class*='allergen']")
                            tag_texts = [tag.text.strip() for tag in tags if tag.text.strip()]
                            
                            if text and not any(skip in text.lower() for skip in ['dining', 'menu', 'home', 'hours', 'contact']):
                                menu_items.append({
                                    'title': text,
                                    'dietary_tags': tag_texts,
                                    'location': 'Unknown Location',
                                    'meal_type': 'Unknown',
                                    'date_string': 'Unknown Date',
                                    'normalized_date': 'unknown',
                                    'link': href,
                                    'source': 'Purdue Dining (Detailed)'
                                })
                                print(f"     -> Menu item: {text} (tags: {tag_texts})")
                    except Exception as e:
                        continue
                
                # Go back to main page
                driver.back()
                time.sleep(2)
                
            except Exception as e:
                print(f"   -> Error clicking element: {e}")
                continue
        
        # Also try to find any JSON data in the page
        page_source = driver.page_source
        json_patterns = [
            r'window\.__MENU_DATA__\s*=\s*(\{.*?\});',
            r'window\.__DINING_DATA__\s*=\s*(\{.*?\});',
            r'"menuItems":\s*(\[.*?\])',
            r'"foodItems":\s*(\[.*?\])'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, page_source, re.DOTALL)
            if matches:
                print(f"   -> Found JSON data with pattern: {pattern}")
                for match in matches:
                    try:
                        data = json.loads(match)
                        # Extract menu items from JSON
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and 'name' in item:
                                    menu_items.append({
                                        'title': item.get('name', 'Unknown Item'),
                                        'dietary_tags': item.get('tags', []),
                                        'location': 'Unknown Location',
                                        'meal_type': 'Unknown',
                                        'date_string': 'Unknown Date',
                                        'normalized_date': 'unknown',
                                        'link': PURDUE_DINING_URL,
                                        'source': 'Purdue Dining (JSON)'
                                    })
                    except:
                        continue
        
    except Exception as e:
        print(f"   [!] Error with Selenium: {e}")
    finally:
        if driver:
            driver.quit()
    
    return menu_items

def scrape_detailed_purdue_dining():
    """Scrape detailed menu items from Purdue dining."""
    print("-> Running Detailed Purdue Dining Scraper...")
    
    # First try the API approach for basic info
    try:
        locations_url = f"{PURDUE_DINING_API_BASE}/locations"
        response = httpx.get(locations_url, timeout=10.0)
        
        if response.status_code != 200:
            print(f"   [!] Error fetching locations: {response.status_code}")
            return []
        
        locations_data = response.json()
        locations = locations_data.get('Location', []) if isinstance(locations_data, dict) else locations_data
        
        # Get basic meal info from API
        basic_menu_items = []
        for location in locations:
            location_name = location.get('Name', 'Unknown Location')
            upcoming_meals = location.get('UpcomingMeals', [])
            
            for meal in upcoming_meals:
                meal_name = meal.get('Name', 'Unknown Meal')
                meal_type = meal.get('Type', 'Unknown')
                start_time = meal.get('StartTime', '')
                end_time = meal.get('EndTime', '')
                
                try:
                    if start_time:
                        start_datetime = parser.parse(start_time)
                        date_string = start_datetime.strftime("%B %d, %Y")
                        normalized_date = start_datetime.strftime("%Y-%m-%d")
                    else:
                        date_string = "Unknown Date"
                        normalized_date = "unknown"
                except:
                    date_string = "Unknown Date"
                    normalized_date = "unknown"
                
                basic_menu_items.append({
                    'title': f"{meal_name} at {location_name}",
                    'description': f"{meal_type} service at {location_name}. Hours: {start_time} - {end_time}",
                    'location': location_name,
                    'meal_type': meal_type,
                    'meal_id': meal.get('ID', ''),
                    'date_string': date_string,
                    'normalized_date': normalized_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'link': PURDUE_DINING_URL,
                    'source': 'Purdue Dining API'
                })
        
        print(f"   -> Found {len(basic_menu_items)} basic menu items from API")
        
        # Now try to get detailed menu items with dietary tags
        detailed_items = _scrape_detailed_menus_with_selenium()
        print(f"   -> Found {len(detailed_items)} detailed menu items with tags")
        
        # Combine both
        all_items = basic_menu_items + detailed_items
        
        return all_items
        
    except Exception as e:
        print(f"   [!] Error with API request: {e}")
        return []

if __name__ == "__main__":
    # Test the scraper
    menu_items = scrape_detailed_purdue_dining()
    print(f"\nTotal menu items found: {len(menu_items)}")
    
    # Show items with dietary tags
    items_with_tags = [item for item in menu_items if item.get('dietary_tags')]
    print(f"Items with dietary tags: {len(items_with_tags)}")
    
    for item in items_with_tags[:5]:
        print(f"Title: {item['title']}")
        print(f"Tags: {item.get('dietary_tags', [])}")
        print("-" * 50)
