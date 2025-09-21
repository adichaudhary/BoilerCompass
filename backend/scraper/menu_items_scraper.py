# backend/scraper/menu_items_scraper.py

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

def _scrape_dining_court_page(driver, court_url, court_name, meal_type):
    """Scrape a specific dining court page for menu items and dietary tags."""
    print(f"   -> Scraping {court_name} ({meal_type})...")
    
    try:
        driver.get(court_url)
        time.sleep(5)  # Wait for page to load
        
        menu_items = []
        
        # Look for menu items with various selectors
        selectors = [
            "[class*='menu-item']",
            "[class*='food-item']", 
            "[class*='item']",
            "[class*='card']",
            "[class*='meal']",
            "[data-testid*='menu']",
            "[data-testid*='item']",
            ".menu-card",
            ".food-card",
            ".item-card"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        text = elem.text.strip()
                        if text and len(text) > 3 and len(text) < 200:
                            # Skip navigation and header text
                            if any(skip in text.lower() for skip in ['dining', 'menu', 'home', 'hours', 'contact', 'back', 'next', 'previous']):
                                continue
                            
                            # Look for dietary tags within this element
                            tags = []
                            tag_elements = elem.find_elements(By.CSS_SELECTOR, "[class*='tag'], [class*='badge'], [class*='label'], [class*='allergen'], [class*='dietary']")
                            for tag_elem in tag_elements:
                                tag_text = tag_elem.text.strip()
                                if tag_text and len(tag_text) < 20:
                                    tags.append(tag_text)
                            
                            # Also look for common dietary indicators in the text
                            dietary_indicators = ['veg', 'vegan', 'halal', 'kosher', 'gluten-free', 'dairy-free', 'soy', 'wheat', 'nuts', 'allergen']
                            for indicator in dietary_indicators:
                                if indicator.lower() in text.lower():
                                    tags.append(indicator)
                            
                            # Special handling for GF items (common abbreviation)
                            if 'gf ' in text.lower() or text.lower().startswith('gf '):
                                tags.append('gluten-free')
                            
                            if text and not any(skip in text.lower() for skip in ['dining', 'menu', 'home', 'hours', 'contact', 'back', 'next', 'previous', 'quick bites', 'on-the-go']):
                                menu_items.append({
                                    'title': text,
                                    'dietary_tags': list(set(tags)),  # Remove duplicates
                                    'location': court_name,
                                    'meal_type': meal_type,
                                    'date_string': 'Today',
                                    'normalized_date': datetime.date.today().strftime('%Y-%m-%d'),
                                    'link': court_url,
                                    'source': 'Purdue Dining (Menu Items)'
                                })
                                print(f"     -> Found: {text} (tags: {tags})")
                    except Exception as e:
                        continue
            except Exception as e:
                continue
        
        # Also look for any JSON data in the page
        page_source = driver.page_source
        json_patterns = [
            r'window\.__MENU_DATA__\s*=\s*(\{.*?\});',
            r'window\.__DINING_DATA__\s*=\s*(\{.*?\});',
            r'"menuItems":\s*(\[.*?\])',
            r'"foodItems":\s*(\[.*?\])',
            r'"items":\s*(\[.*?\])'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, page_source, re.DOTALL)
            if matches:
                print(f"     -> Found JSON data in {court_name}")
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and ('name' in item or 'title' in item):
                                    name = item.get('name') or item.get('title', 'Unknown Item')
                                    tags = item.get('tags', []) or item.get('allergens', []) or item.get('dietary', [])
                                    
                                    menu_items.append({
                                        'title': name,
                                        'dietary_tags': tags if isinstance(tags, list) else [str(tags)],
                                        'location': court_name,
                                        'meal_type': meal_type,
                                        'date_string': 'Today',
                                        'normalized_date': datetime.date.today().strftime('%Y-%m-%d'),
                                        'link': court_url,
                                        'source': 'Purdue Dining (JSON)'
                                    })
                    except:
                        continue
        
        return menu_items
        
    except Exception as e:
        print(f"   -> Error scraping {court_name}: {e}")
        return []

def scrape_detailed_menu_items():
    """Scrape detailed menu items from individual dining court pages."""
    print("-> Running Detailed Menu Items Scraper...")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    driver = None
    all_menu_items = []
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Get today's date for the URLs
        today = datetime.date.today()
        date_str = f"{today.year}/{today.month}/{today.day}"
        
        # Define dining courts and their URLs
        dining_courts = [
            ("Earhart", f"https://dining.purdue.edu/menus/Earhart/{date_str}/", "Lunch"),
            ("Wiley", f"https://dining.purdue.edu/menus/Wiley/{date_str}/", "Dinner"),
            ("Windsor", f"https://dining.purdue.edu/menus/Windsor/{date_str}/", "Lunch"),
            ("Ford", f"https://dining.purdue.edu/menus/Ford/{date_str}/", "Breakfast"),
            ("Hillenbrand", f"https://dining.purdue.edu/menus/Hillenbrand/{date_str}/", "Brunch"),
            ("1Bowl @ Meredith Hall", f"https://dining.purdue.edu/menus/1Bowl%20@%20Meredith%20Hall/{date_str}/", "Lunch"),
            ("Sushi Boss @ Meredith Hall", f"https://dining.purdue.edu/menus/Sushi%20Boss%20@%20Meredith%20Hall/{date_str}/", "Dinner")
        ]
        
        for court_name, court_url, meal_type in dining_courts:
            try:
                items = _scrape_dining_court_page(driver, court_url, court_name, meal_type)
                all_menu_items.extend(items)
                print(f"   -> Found {len(items)} items at {court_name}")
            except Exception as e:
                print(f"   -> Error with {court_name}: {e}")
                continue
        
    except Exception as e:
        print(f"   [!] Error with Selenium: {e}")
    finally:
        if driver:
            driver.quit()
    
    return all_menu_items

if __name__ == "__main__":
    # Test the scraper
    menu_items = scrape_detailed_menu_items()
    print(f"\nTotal menu items found: {len(menu_items)}")
    
    # Show items with dietary tags
    items_with_tags = [item for item in menu_items if item.get('dietary_tags')]
    print(f"Items with dietary tags: {len(items_with_tags)}")
    
    for item in items_with_tags[:10]:
        print(f"Title: {item['title']}")
        print(f"Location: {item['location']}")
        print(f"Tags: {item.get('dietary_tags', [])}")
        print("-" * 50)
    
    # Show all items
    print(f"\nAll items found:")
    for item in menu_items[:20]:
        print(f"- {item['title']} at {item['location']} (tags: {item.get('dietary_tags', [])})")
