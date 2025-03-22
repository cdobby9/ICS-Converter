import re
import spacy
import dateparser
import uuid
from datetime import datetime, timedelta, timezone
from tzlocal import get_localzone
from ics import Calendar, Event

# Load spaCy's English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm' first.")
    exit()

# Get local timezone once
local_tz = get_localzone()

def extract_date(text, reference_date=None):
    """
    Extract date from text using dateparser and regex.
    Handles explicit and relative dates. Returns naive datetime or None.
    """
    try:
        # Use reference date if provided, else current local time
        base_date = reference_date or local_tz.localize(datetime.now()).replace(tzinfo=None)
        
        parsed = dateparser.parse(
            text,
            settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': base_date,
                'RETURN_AS_TIMEZONE_AWARE': False
            }
        )
        
        if parsed:
            # Handle dateparser returning midnight as default time
            return parsed
        else:
            # Fallback to regex for patterns like "19th June"
            match = re.search(
                r'(\d{1,2})(?:st|nd|rd|th)?\s+'
                r'(January|February|March|April|May|June|July|August|'
                r'September|October|November|December)',
                text, re.IGNORECASE
            )
            if match:
                day = int(match.group(1))
                month = match.group(2)
                year = datetime.now().year
                return datetime.strptime(f"{day} {month} {year}", "%d %B %Y")
    except Exception as e:
        print(f"Error parsing date from '{text}': {str(e)}")
    return None

def assign_default_time(segment):
    """Assign default start time based on keywords in the event description."""
    seg_lower = segment.lower()
    if "exam" in seg_lower:
        return (9, 0)  # 9:00 AM
    elif "meeting" in seg_lower or "appointment" in seg_lower:
        return (15, 0)  # 3:00 PM
    return (12, 0)     # 12:00 PM

def process_event_segment(segment, reference_date=None):
    """
    Process a single event segment to extract summary and datetime.
    Returns (summary, datetime) or (None, None) on failure.
    """
    # Use spaCy to remove date/time entities from summary
    doc = nlp(segment)
    date_ents = [ent for ent in doc.ents if ent.label_ in ('DATE', 'TIME')]
    
    # Remove date/time mentions from summary
    summary_text = segment
    for ent in reversed(date_ents):
        summary_text = summary_text[:ent.start_char] + summary_text[ent.end_char:]
    
    # Clean summary text
    summary = re.sub(r'\b(?:I have|on|at)\b', '', summary_text, flags=re.IGNORECASE)
    summary = re.sub(r'\s+', ' ', summary).strip(' ,.-').capitalize()
    if not summary:
        summary = "Scheduled Event"

    # Extract and parse date
    parsed_datetime = extract_date(segment, reference_date)
    if not parsed_datetime:
        return None, None

    return summary, parsed_datetime

def text_to_ics(input_text, output_filename="generated_calendar.ics", use_utc=True):
    """Main function to convert natural language input to ICS file."""
    events = []
    segments = [s.strip() for s in re.split(r'\band\b|\,', input_text) if s.strip()]
    reference_date = None  # Track dates for relative references

    for seg in segments:
        summary, event_datetime = process_event_segment(seg, reference_date)
        if not event_datetime:
            print(f"⚠️ Couldn't parse date from: '{seg}'")
            continue

        # Apply default time if no specific time detected
        if event_datetime.time() == datetime.min.time():
            default_hour, default_min = assign_default_time(seg)
            event_datetime = event_datetime.replace(
                hour=default_hour,
                minute=default_min
            )

        # Localize and convert timezone
        try:
            if event_datetime.tzinfo is None:
                event_datetime = local_tz.localize(event_datetime)
            if use_utc:
                event_datetime = event_datetime.astimezone(timezone.utc)
        except Exception as e:
            print(f"⚠️ Timezone conversion failed for '{seg}': {str(e)}")
            continue

        events.append((summary, event_datetime))
        reference_date = event_datetime  # Update reference for relative dates

    if not events:
        print("❌ No valid events found in input")
        return

    # Create calendar
    cal = Calendar()
    for summary, start_time in events:
        event = Event(
            name=summary,
            begin=start_time,
            end=start_time + timedelta(hours=1),
            uid=f"{uuid.uuid4()}@event.org"
        )
        cal.events.add(event)

    # Write to file
    try:
        with open(output_filename, 'w') as f:
            f.writelines(cal)
        print(f"✅ Successfully created calendar with {len(events)} events at '{output_filename}'")
    except Exception as e:
        print(f"❌ Failed to write ICS file: {str(e)}")

if __name__ == "__main__":
    user_input = input("📅 Enter event descriptions (e.g., 'Dentist appointment tomorrow at 2pm'):\n> ")
    use_utc = input("🌍 Use UTC timezone? [Y/n] ").strip().lower() in ('', 'y', 'yes')
    output_file = input("💾 Output filename [generated_calendar.ics]: ").strip()
    if not output_file:
        output_file = "generated_calendar.ics"
    
    text_to_ics(user_input, output_file, use_utc)