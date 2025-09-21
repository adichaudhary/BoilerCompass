import os
import json
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
from dateutil import parser # NEW: Import the robust date parser

# --- Setup and Configuration ---
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable or use fallback
API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-or-v1-a04109671ed28800f68fbf37ec9fb59c22a01c7deef2d5076a11c7f1bc")

# OpenRouter API URL (using DeepSeek model)
API_URL = "https://openrouter.ai/api/v1/chat/completions"
app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class Question(BaseModel):
    query: str

DATABASE_FILE = os.path.join(os.path.dirname(__file__), 'data', 'database.json')

def load_database():
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return []

def call_deepseek(prompt, max_tokens=500):
    """Call DeepSeek via OpenRouter API with the given prompt"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "BoilerCompass"
    }
    
    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"OpenRouter API error: Invalid API key. Please check your DEEPSEEK_API_KEY")
            raise Exception("Invalid API key. Please get a new key from https://openrouter.ai/")
        elif e.response.status_code == 429:
            print(f"OpenRouter API error: Quota exceeded. Please check your OpenRouter usage limits")
            raise Exception("API quota exceeded. Please check your OpenRouter usage limits")
        else:
            print(f"OpenRouter API error: {e}")
            raise e
    except Exception as e:
        print(f"OpenRouter API error: {e}")
        raise e

# --- API Endpoint ---
@app.post("/api/ask")
async def ask_boilercompass(question: Question):
    all_data = load_database()
    user_query = question.query
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    
    # --- Step 1: Extract Date, Location, and Topic Criteria ---
    # This prompt is now more explicit about ranges and includes dining queries.
    extraction_prompt = f"""
    You are an expert at extracting structured search criteria from a user's query about finding events or dining options.
    The current date is {today_str}.
    Extract the following fields into a JSON object:
    - "startDate": The start of the date range in YYYY-MM-DD format. Example: For "today", use "{today_str}". For "next" queries, use "{today_str}".
    - "endDate": The end of the date range in YYYY-MM-DD format. Example: for "next week", calculate the date 7 days from today. For "next" queries (like "next football game"), use a date 3 months from today. For "this month", calculate the last day of the current month.
    - "location": A specific place mentioned, like "pmu", "union", "virtual", "earhart", "wiley", "windsor". If none or if the query is about sports/teams (like "Purdue football"), use "any".
    - "topic": A specific keyword from the query like "football", "music", "art", "research", "dining", "food", "eat", "meal", "breakfast", "lunch", "dinner", "halal", "kosher", "vegetarian", "vegan", "gluten-free", "allergen". If none, use "any".
    Respond ONLY with a single, valid JSON object.
    User Query: "{user_query}"
    """
    try:
        response = call_deepseek(extraction_prompt, max_tokens=200)
        criteria = json.loads(response.strip().replace('```json', '').replace('```', ''))
    except (Exception, json.JSONDecodeError) as e:
        print(f"   [!] AI criteria extraction failed: {e}")
        # Check if it's a quota exceeded error
        if "quota" in str(e).lower() or "429" in str(e):
            print("   [!] Quota exceeded, using fallback criteria extraction")
            # Simple keyword-based extraction as fallback
            query_lower = user_query.lower()
            if "today" in query_lower:
                criteria = {"startDate": today_str, "endDate": today_str, "location": "any", "topic": "any"}
            elif "tomorrow" in query_lower:
                tomorrow = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                criteria = {"startDate": tomorrow, "endDate": tomorrow, "location": "any", "topic": "any"}
            elif "this week" in query_lower:
                week_end = (today + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                criteria = {"startDate": today_str, "endDate": week_end, "location": "any", "topic": "any"}
            elif "next" in query_lower:
                # For "next" queries, search from today onwards for the next 3 months
                future_end = (today + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
                criteria = {"startDate": today_str, "endDate": future_end, "location": "any", "topic": "any"}
            else:
                criteria = {"startDate": today_str, "endDate": today_str, "location": "any", "topic": "any"}
            
            # Extract topic from query
            if "football" in query_lower:
                criteria["topic"] = "football"
            elif "basketball" in query_lower:
                criteria["topic"] = "basketball"
            elif "music" in query_lower:
                criteria["topic"] = "music"
            elif "art" in query_lower:
                criteria["topic"] = "art"
        else:
            criteria = {"startDate": today_str, "endDate": today_str, "location": "any", "topic": "any"}

    # --- Step 2: Robust Filtering in Python ---
    # NEW: Using the more flexible dateutil.parser instead of strict strptime
    try:
        start_date = parser.parse(criteria.get('startDate', today_str)).date()
        end_date = parser.parse(criteria.get('endDate', start_date.strftime('%Y-%m-%d'))).date()
        
        # If searching for "today", expand to include yesterday for better results
        if criteria.get('startDate') == today_str and criteria.get('endDate') == today_str:
            start_date = today - datetime.timedelta(days=1)  # Include yesterday
    except (ValueError, TypeError, parser.ParserError) as e:
        print(f"   [!] Date parsing failed for criteria. Defaulting to today. Error: {e}")
        start_date, end_date = today, today

    search_location = criteria.get('location', 'any').lower()
    search_topic = criteria.get('topic', 'any').lower()
    
    candidate_events = []
    for event in all_data:
        event_date_str = event.get('normalized_date')
        if event_date_str and event_date_str != 'unknown':
            try:
                event_date = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
                
                date_match = start_date <= event_date <= end_date
                # More flexible location matching - if searching for "purdue", also match events that don't have location info
                location_match = (search_location == 'any' or 
                                search_location in event.get('location', '').lower() or
                                (search_location == 'purdue' and not event.get('location')))
                
                # NEW: More robust topic matching that checks for individual words
                topic_words = search_topic.split()
                event_title_lower = event.get('title', '').lower()
                event_source = event.get('source', '').lower()
                
                # Special handling for dining queries
                if search_topic in ['dining', 'food', 'eat', 'meal', 'breakfast', 'lunch', 'dinner', 'halal', 'kosher', 'vegetarian', 'vegan', 'gluten-free', 'allergen']:
                    # Check if it's a dining item
                    if event_source == 'purdue dining api':
                        topic_match = True
                    # For detailed menu items, check dietary tags
                    elif event_source == 'purdue dining (menu items)':
                        dietary_tags = event.get('dietary_tags', [])
                        if search_topic in ['halal', 'kosher', 'vegetarian', 'vegan', 'gluten-free', 'allergen']:
                            # Check if the dietary tag matches the search
                            topic_match = any(tag.lower() in search_topic.lower() or search_topic.lower() in tag.lower() for tag in dietary_tags)
                            
                            # Special handling for gluten-free queries to also match "gf" in titles
                            if search_topic == 'gluten-free' and not topic_match:
                                topic_match = 'gf' in event_title_lower
                        else:
                            # For general food queries, include all menu items
                            topic_match = True
                    else:
                        topic_match = False
                else:
                    # Require ALL words to be present for better matching
                    topic_match = (search_topic == 'any' or all(word in event_title_lower for word in topic_words))
                
                if date_match and location_match and topic_match:
                    candidate_events.append(event)
            except ValueError:
                continue
    
    if not candidate_events:
        # If searching for football specifically and no results, try other sports
        if search_topic == "football":
            # Look for other sports events in the same time range
            sports_events = []
            for event in all_data:
                event_date_str = event.get('normalized_date')
                if event_date_str and event_date_str != 'unknown':
                    try:
                        event_date = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
                        date_match = start_date <= event_date <= end_date
                        
                        # Check if it's a sports event
                        title_lower = event.get('title', '').lower()
                        is_sports = any(sport in title_lower for sport in ['basketball', 'baseball', 'volleyball', 'soccer', 'tennis', 'hockey', 'wrestling', 'track', 'swimming'])
                        
                        if date_match and is_sports:
                            sports_events.append(event)
                    except ValueError:
                        continue
            
            if sports_events:
                sports_list = ', '.join([f"<b>{event.get('title', 'Unknown Event')}</b>" for event in sports_events[:3]])
                return {"response": f"I couldn't find any football games in that time period, but I found these other sports events: {sports_list}. Would you like to know more about any of these?"}
            else:
                return {"response": "I couldn't find any football games in that time period. The next football game might not be scheduled yet, or it could be outside the current data range. You might want to check the official Purdue Athletics schedule."}
        else:
            return {"response": "I couldn't find any events that match your criteria. Try asking something simpler, like 'what's happening today?'"}

    # --- Step 3: Final AI Response Generation ---
    response_prompt = f"""
    You are BoilerCompass, a friendly and helpful AI guide for Purdue University.
    A user asked: "{user_query}"
    Based ONLY on the following data I have provided, create a conversational summary.
    - If there's only one item, describe it.
    - If there are multiple items, summarize them nicely.
    - Do not invent any details.
    - Use HTML formatting with <b>bold</b> tags for emphasis instead of asterisks
    - Use <br> tags for line breaks instead of newlines
    - Format dates, times, and locations clearly
    - For football games, include opponent names and locations prominently
    - For dining options, include meal times, locations, and meal types clearly
    - If showing dining options, group them by location or meal type for better organization
    - For dietary restriction queries (halal, kosher, vegetarian, vegan, gluten-free), show specific menu items that match those dietary requirements
    - Include dietary tags and allergen information when available
    - If no specific dietary items are found, mention that dietary information may be limited and suggest contacting dining services directly
    
    Data:
    {json.dumps(candidate_events[:20])}
    """
    try:
        final_response = call_deepseek(response_prompt, max_tokens=1500)
        return {"response": final_response}
    except Exception as e:
        print(f"   [!] Error during final response generation: {e}")
        print(f"   [!] Error type: {type(e).__name__}")
        import traceback
        print(f"   [!] Full traceback: {traceback.format_exc()}")
        
        # Check if it's a quota exceeded error
        if "quota" in str(e).lower() or "429" in str(e):
            # Provide a fallback response based on the events data
            if candidate_events:
                event_summaries = []
                for event in candidate_events[:5]:  # Show first 5 events
                    event_summaries.append(f"• <b>{event.get('title', 'Unknown Event')}</b> at {event.get('location', 'Unknown Location')}")
                
                fallback_response = f"I found <b>{len(candidate_events)}</b> events that match your query:<br><br>" + "<br>".join(event_summaries)
                if len(candidate_events) > 5:
                    fallback_response += f"<br><br>...and <b>{len(candidate_events) - 5}</b> more events. Check the full list for more details!"
                
                return {"response": fallback_response}
            else:
                return {"response": "I couldn't find any events matching your criteria. The AI service is currently unavailable due to quota limits, but you can check the events data directly."}
        else:
            return {"response": "Sorry, I had a problem thinking of a response. Please try again!"}

