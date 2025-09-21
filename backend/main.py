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
API_KEY = "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"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class Question(BaseModel):
    query: str

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'events.json')

def load_events():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return []

def call_groq(prompt, max_tokens=500):
    """Call Groq API with the given prompt"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Groq API error: {e}")
        raise e

# --- API Endpoint ---
@app.post("/api/ask")
async def ask_boilercompass(question: Question):
    all_events = load_events()
    user_query = question.query
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    
    # --- Step 1: Extract Date, Location, and Topic Criteria ---
    # This prompt is now more explicit about ranges.
    extraction_prompt = f"""
    You are an expert at extracting structured search criteria from a user's query about finding events.
    The current date is {today_str}.
    Extract the following fields into a JSON object:
    - "startDate": The start of the date range in YYYY-MM-DD format. Example: For "today", use "{today_str}".
    - "endDate": The end of the date range in YYYY-MM-DD format. Example: for "next week", calculate the date 7 days from today. For "this month", calculate the last day of the current month.
    - "location": A specific place mentioned, like "pmu", "union", "virtual". If none or if the query is about sports/teams (like "Purdue football"), use "any".
    - "topic": A specific keyword from the query like "football", "music", "art", "research". If none, use "any".
    Respond ONLY with a single, valid JSON object.
    User Query: "{user_query}"
    """
    try:
        response = call_groq(extraction_prompt, max_tokens=200)
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
    except (ValueError, TypeError, parser.ParserError) as e:
        print(f"   [!] Date parsing failed for criteria. Defaulting to today. Error: {e}")
        start_date, end_date = today, today

    search_location = criteria.get('location', 'any').lower()
    search_topic = criteria.get('topic', 'any').lower()
    
    candidate_events = []
    for event in all_events:
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
                # Require ALL words to be present for better matching
                topic_match = (search_topic == 'any' or all(word in event_title_lower for word in topic_words))
                
                if date_match and location_match and topic_match:
                    candidate_events.append(event)
            except ValueError:
                continue
    
    if not candidate_events:
        return {"response": "I couldn't find any events that match your criteria. Try asking something simpler, like 'what's happening today?'"}

    # --- Step 3: Final AI Response Generation ---
    response_prompt = f"""
    You are BoilerCompass, a friendly and helpful AI guide for Purdue University.
    A user asked: "{user_query}"
    Based ONLY on the following event data I have provided, create a conversational summary.
    - If there's only one event, describe it.
    - If there are multiple events, summarize them nicely.
    - Do not invent any details.
    
    Event Data:
    {json.dumps(candidate_events[:20])}
    """
    try:
        final_response = call_groq(response_prompt, max_tokens=500)
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
                    event_summaries.append(f"• {event.get('title', 'Unknown Event')} at {event.get('location', 'Unknown Location')}")
                
                fallback_response = f"I found {len(candidate_events)} events that match your query:\n\n" + "\n".join(event_summaries)
                if len(candidate_events) > 5:
                    fallback_response += f"\n\n...and {len(candidate_events) - 5} more events. Check the full list for more details!"
                
                return {"response": fallback_response}
            else:
                return {"response": "I couldn't find any events matching your criteria. The AI service is currently unavailable due to quota limits, but you can check the events data directly."}
        else:
            return {"response": "Sorry, I had a problem thinking of a response. Please try again!"}

