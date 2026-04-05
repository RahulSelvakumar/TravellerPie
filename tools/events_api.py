# tools/events_api.py
import json

def get_local_events(city: str, month: str) -> str:
    """
    Scans global event calendars to provide proactive inspiration.
    """
    # A mocked database for high-quality hackathon demo data
    mock_event_db = {
        "tokyo": {
            "april": [
                {"event": "Cherry Blossom Festival", "type": "Cultural", "vibe": "Scenic, Crowded"},
                {"event": "Web3 & AI Summit Tokyo", "type": "Tech Conference", "vibe": "Professional, Networking"}
            ]
        },
        "bengaluru": {
            "may": [
                {"event": "Startup Pitch Night", "type": "Tech", "vibe": "High Energy"},
                {"event": "Cubbon Park Weekend Run", "type": "Fitness", "vibe": "Outdoor, Active"}
            ]
        }
    }
    
    city_key = city.lower()
    month_key = month.lower()
    
    events = mock_event_db.get(city_key, {}).get(month_key)
    
    if events:
        return json.dumps({"status": "events_found", "events": events})
    else:
        # If we don't have mock data, instruct the AI to use the Search Tool instead!
        return json.dumps({"status": "no_database_events", "suggestion": "Use google_search tool to find events."})

if __name__ == "__main__":
    print(get_local_events("Tokyo", "April"))