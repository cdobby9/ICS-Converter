import re
import spacy
import dateparser
import uuid
from datetime import datetime, timedelta, timezone
from tzlocal import get_localzone
from ics import Calendar, Event

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Spacy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm' first.")
    exit()

local_tz = get_localzone()

def assign_default_time(segment):
    seg_lower = segment.lower()
    if "exam" in seg_lower:
        return (9, 0)
    elif "meeting" in seg_lower or "appointment" in seg_lower:
        return (15, 0)
    return (12, 0)

def extract_date(text, reference_date=None, current_date=None):
    try:
        chainable = False
        lowered = text.lower()
        current_date = current_date or datetime.now(local_tz).replace(tzinfo=None)
        
        if "the day after" in lowered:
            chainable = True
            base_date = reference_date or current_date
            parsed_date = base_date + timedelta(days=1)
            return parsed_date.replace(tzinfo=None), chainable
        
        if "tomorrow" in lowered:
            return (current_date + timedelta(days=1)).replace(tzinfo=None), False
        
        if "next week" in lowered:
            return (current_date + timedelta(weeks=1)).replace(tzinfo=None), False

        datetime_pattern = r'''
            (\d{1,2})(?:st|nd|rd|th)?\s+
            (January|February|March|April|May|June|July|August|
            September|October|November|December)
            (?:\s+(\d{4}))?
            (?:\s+at\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)?)?
        '''
        match = re.search(datetime_pattern, text, re.IGNORECASE | re.VERBOSE)
        if match:
            day, month, year, hour, minute, period = match.groups()
            year = int(year) if year else current_date.year
            date_obj = datetime.strptime(f"{day} {month} {year}", "%d %B %Y")
            
            if hour:
                hour = int(hour)
                minute = int(minute) if minute else 0
                if period and 'pm' in period.lower() and hour < 12:
                    hour += 12
                elif period and 'am' in period.lower() and hour == 12:
                    hour = 0
                date_obj = date_obj.replace(hour=hour, minute=minute)
            
            return date_obj.replace(tzinfo=None), False

        weekday_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        for day, num in weekday_map.items():
            if day in lowered:
                days_ahead = (num - current_date.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                parsed_date = current_date + timedelta(days=days_ahead)
                return parsed_date.replace(tzinfo=None), False

        parsed = dateparser.parse(
            text,
            settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': current_date,
                'RETURN_AS_TIMEZONE_AWARE': False
            }
        )
        return (parsed.replace(tzinfo=None), False) if parsed else (None, False)

    except Exception as e:
        print(f"Date error: {str(e)}")
        return None, False

def process_event_segment(segment, reference_date=None, current_date=None):
    if re.match(r'^\s*(also|don\'?t forget|and)\s*$', segment, re.IGNORECASE):
        return None, None, False

    doc = nlp(segment)
    date_ents = [ent for ent in doc.ents if ent.label_ in ('DATE', 'TIME')]
    summary_text = segment
    for ent in reversed(date_ents):
        summary_text = summary_text[:ent.start_char] + summary_text[ent.end_char:]
    
    summary = re.sub(
        r'\b(?:I have|on|at|the day after|a|also|don\'?t forget|next week|tomorrow|morning|after)\b', 
        '', summary_text, flags=re.IGNORECASE
    )
    summary = re.sub(r'[,\-\.]+$', '', summary).strip().capitalize()
    if not summary:
        summary = "Scheduled Event"

    parsed_datetime, chainable = extract_date(segment, reference_date, current_date)
    if not parsed_datetime:
        return None, None, False

    if parsed_datetime.time() == datetime.min.time():
        default_hour, default_min = assign_default_time(segment)
        parsed_datetime = parsed_datetime.replace(hour=default_hour, minute=default_min)

    return summary, parsed_datetime.replace(tzinfo=local_tz), chainable

def text_to_ics(input_text, output_filename="generated_calendar.ics", use_utc=True):
    current_date = datetime.now(local_tz).replace(tzinfo=None)
    segments = [
        s.strip() for s in 
        re.split(r'\s*(?:,|\.\s| and )\s*', input_text)
        if len(s.strip()) > 8
    ]
    
    events = []
    reference_date = None

    for seg in segments:
        summary, event_datetime, chainable = process_event_segment(
            seg, reference_date, current_date
        )
        if not event_datetime:
            print(f"⚠️ Couldn't parse: '{seg}'")
            continue

        if use_utc:
            event_datetime = event_datetime.astimezone(timezone.utc)

        events.append((summary, event_datetime))
        if chainable:
            reference_date = event_datetime

    if not events:
        print("❌ No events found")
        return

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
        print(f"✅ Created '{output_filename}' with {len(events)} events")
    except Exception as e:
        print(f"❌ Save failed: {str(e)}")

if __name__ == "__main__":
    user_input = input("📅 Enter events:\n> ")
    use_utc = input("🌍 Use UTC timezone? [Y/n] ").strip().lower() in ('', 'y', 'yes')
    output_file = input("💾 Output filename [generated_calendar.ics]: ").strip()
    if not output_file:
        output_file = "generated_calendar.ics"
    
    text_to_ics(user_input, output_file, use_utc)