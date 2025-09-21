# backend/scraper/purdue_sports_scraper.py

import httpx
from bs4 import BeautifulSoup
import datetime
from dateutil import parser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def _normalize_date(date_str):
    """Normalize date string to YYYY-MM-DD format."""
    if not date_str or date_str == "No Date":
        return "unknown"
    try:
        parsed_date = parser.parse(date_str)
        return parsed_date.strftime('%Y-%m-%d')
    except (ValueError, TypeError, parser.ParserError):
        return "unknown"

def _setup_selenium_driver():
    """Setup Chrome driver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"   [!] Error setting up Chrome driver: {e}")
        print("   [!] Make sure Chrome and ChromeDriver are installed")
        return None

def _scrape_football_schedule(driver):
    """Scrape football schedule using Selenium."""
    print("   -> Scraping football schedule...")
    
    try:
        driver.get("https://purduesports.com/sports/football/schedule")
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 20)
        
        # Wait for schedule content to load
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except TimeoutException:
            print("   [!] Timeout waiting for page to load")
            return []
        
        # Give extra time for JavaScript to load content
        time.sleep(5)
        
        # Look for schedule elements
        schedule_elements = driver.find_elements(By.CSS_SELECTOR, 
            'div[class*="schedule"], tr[class*="schedule"], div[class*="game"], tr[class*="game"], div[class*="event"], tr[class*="event"]')
        
        print(f"   -> Found {len(schedule_elements)} potential schedule elements")
        
        events = []
        
        for element in schedule_elements:
            try:
                # Extract text content
                text = element.text.strip()
                if not text or len(text) < 10:
                    continue
                
                # Look for game patterns in the text
                if any(keyword in text.lower() for keyword in ['vs', 'at', 'purdue', 'football']):
                    # Try to extract structured data
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    title = "No Title"
                    date_str = "No Date"
                    location = "No Location"
                    
                    # Look for opponent/team name - try multiple approaches
                    opponent_found = False
                    for line in lines:
                        line_lower = line.lower()
                        # Look for vs/at patterns
                        if any(keyword in line_lower for keyword in ['vs', 'at']) and len(line) > 5:
                            title = line
                            opponent_found = True
                            break
                        # Look for team names that might be standalone
                        elif any(team in line_lower for team in ['ball state', 'ohio state', 'michigan', 'indiana', 'illinois', 'iowa', 'minnesota', 'nebraska', 'northwestern', 'wisconsin', 'maryland', 'rutgers', 'penn state', 'michigan state']) and len(line) > 3:
                            title = line
                            opponent_found = True
                            break
                    
                    # If no opponent found in lines, try to extract from the full text
                    if not opponent_found:
                        full_text_lower = text.lower()
                        # Look for common opponent patterns
                        opponent_patterns = [
                            'vs ball state', 'at ball state', 'ball state',
                            'vs ohio state', 'at ohio state', 'ohio state',
                            'vs michigan', 'at michigan', 'michigan',
                            'vs indiana', 'at indiana', 'indiana',
                            'vs illinois', 'at illinois', 'illinois',
                            'vs iowa', 'at iowa', 'iowa',
                            'vs minnesota', 'at minnesota', 'minnesota',
                            'vs nebraska', 'at nebraska', 'nebraska',
                            'vs northwestern', 'at northwestern', 'northwestern',
                            'vs wisconsin', 'at wisconsin', 'wisconsin',
                            'vs maryland', 'at maryland', 'maryland',
                            'vs rutgers', 'at rutgers', 'rutgers',
                            'vs penn state', 'at penn state', 'penn state',
                            'vs michigan state', 'at michigan state', 'michigan state'
                        ]
                        
                        for pattern in opponent_patterns:
                            if pattern in full_text_lower:
                                # Find the actual text with proper capitalization
                                import re
                                match = re.search(pattern, text, re.IGNORECASE)
                                if match:
                                    title = match.group(0)
                                    opponent_found = True
                                    break
                    
                    # Look for date
                    for line in lines:
                        if any(char.isdigit() for char in line) and any(month in line.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                            date_str = line
                            break
                    
                    # Look for location - try multiple approaches
                    for line in lines:
                        line_lower = line.lower()
                        if any(keyword in line_lower for keyword in ['stadium', 'arena', 'field', 'home', 'away', 'west lafayette', 'ross-ade', 'ross ade']):
                            location = line
                            break
                        # Look for specific venue names
                        elif any(venue in line_lower for venue in ['ross-ade stadium', 'ross ade stadium', 'memorial stadium', 'kinnick stadium', 'huntington bank stadium']):
                            location = line
                            break
                    
                    # If no specific location found, determine if it's home or away
                    if location == "No Location":
                        # Check if it's a home game by looking for Purdue-related keywords
                        if any(keyword in text.lower() for keyword in ['purdue', 'west lafayette', 'home', 'ross-ade', 'ross ade']):
                            location = "West Lafayette, IN"
                        elif any(keyword in text.lower() for keyword in ['at', 'away', 'seattle', 'washington', 'minnesota', 'michigan', 'ohio state', 'indiana']):
                            # Try to extract the away location
                            if 'seattle' in text.lower() or 'washington' in text.lower():
                                location = "Seattle, WA"
                            elif 'minnesota' in text.lower():
                                location = "Minneapolis, MN"
                            elif 'michigan' in text.lower():
                                location = "Ann Arbor, MI"
                            elif 'ohio state' in text.lower():
                                location = "Columbus, OH"
                            elif 'indiana' in text.lower():
                                location = "Bloomington, IN"
                            else:
                                location = "Away"
                        else:
                            location = "West Lafayette, IN"  # Default to home
                    
                    normalized_date = _normalize_date(date_str)
                    
                    if title != "No Title" and normalized_date != "unknown":
                        # Clean up the title
                        clean_title = title.strip()
                        
                        # Skip non-game items
                        if any(skip in clean_title.lower() for skip in ['live stats', 'schedule stats', 'stats', 'ticket', 'watch', 'listen']):
                            continue
                        
                        # Create a proper game title based on location
                        if 'vs' in clean_title.lower() or 'at' in clean_title.lower():
                            game_title = f"Purdue Football {clean_title}"
                        elif clean_title.upper() in ['BALL STATE', 'OHIO STATE', 'MICHIGAN', 'INDIANA', 'ILLINOIS', 'IOWA', 'MINNESOTA', 'NEBRASKAN', 'NORTHWESTERN', 'WISCONSIN', 'MARYLAND', 'RUTGERS', 'PENN STATE', 'MICHIGAN STATE']:
                            # Determine if home or away based on location
                            if location == "West Lafayette, IN" or "west lafayette" in location.lower():
                                game_title = f"Purdue Football vs {clean_title}"
                            else:
                                game_title = f"Purdue Football at {clean_title}"
                        elif clean_title == 'Seattle, Wash.':
                            game_title = "Purdue Football at Washington"
                        elif any(team in clean_title.lower() for team in ['ball state', 'ohio state', 'michigan', 'indiana', 'illinois', 'iowa', 'minnesota', 'nebraska', 'northwestern', 'wisconsin', 'maryland', 'rutgers', 'penn state', 'michigan state']):
                            # Determine if home or away based on location
                            if location == "West Lafayette, IN" or "west lafayette" in location.lower():
                                game_title = f"Purdue Football vs {clean_title}"
                            else:
                                game_title = f"Purdue Football at {clean_title}"
                        else:
                            game_title = f"Purdue Football {clean_title}"
                        
                        # Check for duplicates
                        if not any(e['title'] == game_title and e['normalized_date'] == normalized_date for e in events):
                            events.append({
                                'title': game_title,
                                'date_string': date_str,
                                'normalized_date': normalized_date,
                                'location': location if location != "No Location" else "TBD",
                                'link': "https://purduesports.com/sports/football/schedule",
                                'source': 'Purdue Sports'
                            })
                            print(f"   -> Added: {game_title} on {normalized_date}")
                
            except Exception as e:
                print(f"   [!] Error parsing element: {e}")
                continue
        
        return events
        
    except Exception as e:
        print(f"   [!] Error scraping football schedule: {e}")
        return []

def scrape_purdue_sports():
    """Scrape real sports events from Purdue Athletics website using Selenium."""
    print("-> Running Purdue Sports Scraper (Selenium)...")
    
    driver = _setup_selenium_driver()
    if not driver:
        print("   [!] Could not setup Selenium driver, falling back to basic scraping")
        return []
    
    all_events = []
    
    try:
        # Focus on football first since that's what users ask about most
        football_events = _scrape_football_schedule(driver)
        all_events.extend(football_events)
        
    finally:
        driver.quit()
    
    print(f"   -> Found {len(all_events)} real sports events.")
    return all_events