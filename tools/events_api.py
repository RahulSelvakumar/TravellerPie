import json
def get_local_events(city: str, month: str) -> str:
    db = {
        "tokyo": {"april": [{"event": "Cherry Blossom Festival", "type": "Cultural"}]},
        "bengaluru": {"may": [{"event": "Startup Pitch Night", "type": "Tech"}]}
    }
    events = db.get(city.lower(), {}).get(month.lower())
    return json.dumps({"events": events}) if events else "Use google_search to find events."