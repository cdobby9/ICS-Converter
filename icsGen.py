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

local_tz = get_localzone()

def assign_default_time(segment):
    """Assign default start time based on keywords in the event description."""
    seg_lower = segment.lower()
    if "exam" in seg_lower:
        return (9, 0)  # 9:00 AM
    elif "meeting" in seg_lower or "appointment" in seg_lower:
        return (15, 0)  # 3:00 PM
    return (12, 0)     # 12:00 PM

def extract_date(text, reference_date=None):
    """Enhanced date parser with improved relative date handling."""
    try:
        base_date = reference_date or datetime.now(local_tz).replace(tzinfo=None)
        lowered = text.lower()
        
        # Handle relative phrases
        if "the day after" in lowered:
            return base_date + timedelta(days=2)
        if "tomorrow" in lowered:
            return base_date + timedelta(days=1)
        if "next week" in lowered:
            return base_date + timedelta(weeks=1)
            
        # Handle weekdays
        weekday_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        for day, num in weekday_map.items():
            if day in lowered:
                days_ahead = (num - base_date.weekday()) % 7
                if days_ahead == 0:  # Today is the weekday
                    days_ahead = 7
                return base_date + timedelta(days=days_ahead)

        # Extract time first
        time_match = re.search(r'(\d{1,2})(:\d{2})?\s*(am|pm)?', text, re.IGNORECASE)
        parsed_time = None
        if time_match:
            time_str = time_match.group(0)
            parsed_time = dateparser.parse(time_str)

        # Parse full date
        parsed = dateparser.parse(
            text,
            settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': base_date,
                'RETURN_AS_TIMEZONE_AWARE': False
            }
        )

        # Combine date and time components
        if parsed:
            if parsed_time and parsed.time() == datetime.min.time():
                parsed = parsed.replace(
                    hour=parsed_time.hour,
                    minute=parsed_time.minute
                )
            return parsed.replace(tzinfo=None)

        # Fallback to explicit date patterns
        date_pattern = r'''
            (\d{1,2})(?:st|nd|rd|th)?\s+
            (January|February|March|April|May|June|July|August|
            September|October|November|December)
            (?:\s+(\d{4}))?
        '''
        match = re.search(date_pattern, text, re.IGNORECASE | re.VERBOSE)
        if match:
            day, month, year = match.groups()
            year = int(year) if year else base_date.year
            return datetime.strptime(f"{day} {month} {year}", "%d %B %Y")

    except Exception as e:
        print(f"Date parsing error: {str(e)}")
    return None

def process_event_segment(segment, reference_date=None):
    """Process event segment with comprehensive cleaning."""
    doc = nlp(segment)
    
    # Extract and clean summary
    date_ents = [ent for ent in doc.ents if ent.label_ in ('DATE', 'TIME')]
    summary_text = segment
    for ent in reversed(date_ents):
        summary_text = summary_text[:ent.start_char] + summary_text[ent.end_char:]
    
    summary = re.sub(
        r'\b(?:I have|on|at|also|don\'?t forget|and|a)\b', 
        '', 
        summary_text, 
        flags=re.IGNORECASE
    )
    summary = re.sub(r'[,\-\.]+$', '', summary).strip().capitalize()
    if not summary:
        summary = "Scheduled Event"

    # Parse date/time
    parsed_datetime = extract_date(segment, reference_date)
    if not parsed_datetime:
        return None, None

    # Apply default time if needed
    try:
        if parsed_datetime.time() == datetime.min.time():
            default_hour, default_min = assign_default_time(segment)
            parsed_datetime = parsed_datetime.replace(
                hour=default_hour,
                minute=default_min
            )
    except Exception as e:
        print(f"⚠️ Time assignment error in '{segment}': {str(e)}")
        return None, None

    return summary, parsed_datetime.replace(tzinfo=local_tz)

def text_to_ics(input_text, output_filename="generated_calendar.ics", use_utc=True):
    """Main conversion function with robust error handling."""
    # Split input into segments
    segments = re.split(r'\s*(?:,|and|\.)\s*', input_text)
    segments = [s.strip() for s in segments if s.strip()]
    
    events = []
    reference_date = None

    for seg in segments:
        if not seg:
            continue
            
        summary, event_datetime = process_event_segment(seg, reference_date)
        if not event_datetime:
            print(f"⚠️ Couldn't parse date from: '{seg}'")
            continue

        # Convert to UTC if requested
        if use_utc:
            try:
                event_datetime = event_datetime.astimezone(timezone.utc)
            except Exception as e:
                print(f"⚠️ Timezone conversion failed for '{seg}': {str(e)}")
                continue

        events.append((summary, event_datetime))
        reference_date = event_datetime  # Update reference date

    if not events:
        print("❌ No valid events found in input")
        return

    # Create and save calendar
    cal = Calendar()
    for summary, start_time in events:
        event = Event(
            name=summary,
            begin=start_time,
            end=start_time + timedelta(hours=1),
            uid=f"{uuid.uuid4()}@event.org"
        )
        cal.events.add(event)

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