import re
import spacy
import dateparser
import uuid
from datetime import datetime, timedelta
from ics import Calendar, Event

# Load spaCy's English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm' first.")
    exit()

def extract_date(text, reference_date=None):
    """
    Extract an explicit date from text.
    Handles phrases like "19th June" and relative words like "tomorrow" or "the day after".
    """
    today = datetime.today()
    
    # Handle relative dates explicitly:
    lowered = text.lower()
    if "the day after" in lowered:
        if reference_date:
            return reference_date + timedelta(days=1)
        else:
            return today + timedelta(days=1)
    if "tomorrow" in lowered:
        if reference_date:
            return reference_date + timedelta(days=1)
        else:
            return today + timedelta(days=1)
    
    # Try using dateparser first
    parsed = dateparser.parse(text, settings={'PREFER_DATES_FROM': 'future'})
    if parsed:
        return parsed

    # Fallback: use regex to match explicit dates like "19th June"
    match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)', text, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month = match.group(2)
        year = today.year  # assume current year
        try:
            return datetime.strptime(f"{day} {month} {year}", "%d %B %Y")
        except ValueError:
            return None
    return None

def assign_default_time(segment):
    """Assign default start times based on keywords in the event segment."""
    seg = segment.lower()
    if "exam" in seg:
        return "09:00"  # Exams at 9 AM
    elif "meeting" in seg or "appointment" in seg:
        return "15:00"  # Meetings at 3 PM
    else:
        return "12:00"  # Default noon

def process_event_segment(segment, reference_date=None):
    """
    Process one event segment and extract a summary and a date.
    Returns (summary, event_date) or (None, None) if no date is found.
    """
    event_date = extract_date(segment, reference_date)
    if not event_date:
        return None, None

    # Clean the segment to form a concise event summary.
    # Remove explicit date phrases
    summary = re.sub(r'\d{1,2}(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)', '', segment, flags=re.IGNORECASE)
    summary = re.sub(r'\b(tomorrow|the day after)\b', '', summary, flags=re.IGNORECASE)
    # Remove extra words that are less meaningful
    summary = summary.replace("I have", "").replace("on", "")
    # Remove extra whitespace and punctuation
    summary = " ".join(summary.split()).strip(" ,.")
    # Capitalize first letter
    summary = summary.capitalize()
    
    return summary, event_date

def text_to_ics(input_text, output_filename="generated_calendar.ics"):
    """
    Converts free-form text into an ICS file.
    Splits the input on " and " and processes each segment.
    Uses a reference date so that relative dates (e.g., "the day after")
    follow the previous event.
    """
    segments = input_text.split(" and ")
    events = []
    last_date = None

    for seg in segments:
        summary, event_date = process_event_segment(seg, last_date)
        if event_date:
            last_date = event_date  # update reference for relative dates
            events.append((summary, event_date, seg))
        else:
            print(f"Warning: No valid date found in segment: '{seg}'")

    if not events:
        print("No events found in the input.")
        return

    cal = Calendar()

    for summary, event_date, seg in events:
        start_time_str = assign_default_time(seg)
        event_date_str = event_date.strftime("%Y-%m-%d")
        start_datetime = datetime.strptime(f"{event_date_str} {start_time_str}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + timedelta(hours=1)  # default duration is 1 hour

        e = Event()
        e.name = summary
        # Format times in UTC (you can remove the 'Z' if you prefer local time)
        e.begin = start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        e.end = end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        e.uid = f"{uuid.uuid4()}@event.org"
        cal.events.add(e)

    with open(output_filename, "w") as f:
        f.writelines(cal)
    print(f"ICS file '{output_filename}' created successfully!")

if __name__ == "__main__":
    user_input = input("Enter your event details: ")
    text_to_ics(user_input)
