# tools/transit_api.py

def check_transit_status(flight_or_train_number: str) -> dict:
    """
    Checks the real-time status of a transit vehicle.
    (Simulated for hackathon reliability).
    """
    # DEMO TRIGGER: If the AI checks this specific flight, force a delay to show off the system's pivot capability!
    if flight_or_train_number.upper() == "DELAY-123":
        return {
            "transit_id": flight_or_train_number,
            "status": "Delayed",
            "delay_duration": "3 Hours",
            "reason": "Severe weather at destination",
            "new_arrival_time": "23:00 PM (Requires late hotel check-in)"
        }
        
    # Normal status for everything else
    return {
        "transit_id": flight_or_train_number,
        "status": "On Time",
        "delay_duration": "0 Minutes",
        "reason": "N/A",
        "new_arrival_time": "As Scheduled"
    }

if __name__ == "__main__":
    print(check_transit_status("DELAY-123"))
    print(check_transit_status("FLIGHT-999"))