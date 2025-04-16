import sys
from google import genai
import os
import json
from taskie.logger import logger
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from taskie.prompt import generate_task_prompt


DEFAULT_EVENT_DURATION_MINUTES = 60
FIND_NEXT_SLOT_INCREMENT_MINUTES = 30
FIND_NEXT_SLOT_MAX_HOURS = 4
TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
TOKEN_REFRESH_URL = "https://oauth2.googleapis.com/token"


def gemini_response(prompt: str):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"{prompt}"
    )

    return response


def sanitize_gemini_response(response):
    cleaned_response_text = response.text.strip().strip('`').strip()
    if cleaned_response_text.lower().startswith("json"):
        cleaned_response_text = cleaned_response_text[4:].strip()

    print(f"Gemini Raw Response:\n{cleaned_response_text}")
    sanitized_response = json.loads(cleaned_response_text)

    if not all(k in sanitized_response for k in ["summary", "start_time", "end_time", "description"]):
        raise ValueError("Gemini response missing required keys.")
    if not sanitized_response.get("summary") or not sanitized_response.get("start_time") or not sanitized_response.get("end_time"):
        raise ValueError("Gemini response has empty essential values (summary, start_time, end_time).")

    try:
        dateutil_parser.isoparse(sanitized_response["start_time"])
        dateutil_parser.isoparse(sanitized_response["end_time"])
    except ValueError as date_err:
        raise ValueError(f"Gemini returned invalid ISO 8601 date format: {date_err}. Response: {cleaned_response_text}")

    return sanitized_response


def is_slot_free(service, start_time_iso, end_time_iso, calendar_id='primary') -> bool:
    """Checks if a time slot is free using the freebusy API."""
    print(f"Checking availability from {start_time_iso} to {end_time_iso}...")
    try:
        # Use timezone from start_time string for the query
        tz_info = dateutil_parser.isoparse(start_time_iso).tzinfo
        tz_str = str(tz_info) if tz_info else 'UTC'  # Default to UTC if no tz info

        freebusy_query = {
            "timeMin": start_time_iso,
            "timeMax": end_time_iso,
            "timeZone": tz_str,
            "items": [{"id": calendar_id}]
        }
        try:
            results = service.freebusy().query(body=freebusy_query).execute()
        except Exception as e:
            print(f"Error executing free busy query {e}")
            return False

        calendar_busy_times = results.get('calendars', {}) \
            .get(calendar_id, {}) \
            .get('busy', [])

        if not calendar_busy_times:
            print("Slot is free.")
            return True
        else:
            # For simplicity, any overlap is considered busy here.
            print(f"Slot is busy. Conflicts: {calendar_busy_times}")
            return False

    except HttpError as error:
        print(f"An API error occurred during free/busy check: {error}",
              file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred during free/busy check: {e}",
              file=sys.stderr)
        return False


def find_next_free_slot(
        service, original_start_dt, original_end_dt, calendar_id='primary'):
    """Finds the next available time slot of the same duration."""
    duration = original_end_dt - original_start_dt
    # Start searching right after the originally proposed end time,
    # ensuring we maintain the original timezone info.
    current_start_dt = original_end_dt
    search_limit_dt = original_start_dt + relativedelta(hours=FIND_NEXT_SLOT_MAX_HOURS)

    print(f"\nSearching for the next free slot with duration {duration}...")

    while current_start_dt < search_limit_dt:
        current_end_dt = current_start_dt + duration
        start_iso = current_start_dt.isoformat()
        end_iso = current_end_dt.isoformat()

        if is_slot_free(service, start_iso, end_iso, calendar_id):
            print(f"Found next available slot: {start_iso} to {end_iso}")
            return start_iso, end_iso

        current_start_dt += relativedelta(minutes=FIND_NEXT_SLOT_INCREMENT_MINUTES)

    print(f"Could not find a free slot within the next {FIND_NEXT_SLOT_MAX_HOURS} hours.", file=sys.stderr)
    return None, None


# Add task to google calender
def my_taskie(redis_client, task, user_id) -> bool:
    prompt = generate_task_prompt(task)
    response = gemini_response(prompt)
    sanitized_response = sanitize_gemini_response(response)

    summary = sanitized_response['summary']
    start_iso = sanitized_response['start_time']
    end_iso = sanitized_response['end_time']
    description = sanitized_response['description']
    calendar_id = "primary"

    try:
        start_dt = dateutil_parser.isoparse(start_iso)
        end_dt = dateutil_parser.isoparse(end_iso)
    except ValueError as e:
        print(f"ERROR: Could not parse date/time from Gemini: {e}",
              file=sys.stderr)
        return False

    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    access_token = redis_client.get(f"access_token:{user_id}")
    refresh_token = redis_client.get(f"refresh_token:{user_id}")

    credentials = Credentials(
        token=access_token,
        token_uri=TOKEN_REFRESH_URL,
        refresh_token=refresh_token,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )

    try:
        service = build('calendar', 'v3', credentials=credentials)
    except Exception as build_error:
        print(f"Failed to build Google Calendar service client: {build_error}",
              file=sys.stderr)
        return False

    if not is_slot_free(service, start_iso, end_iso, calendar_id):
        new_start_iso, new_end_iso = find_next_free_slot(
            service,
            start_dt,
            end_dt,
            calendar_id)
        if not new_start_iso:
            logger.fatal("Failed to find an alternative slot. Event not added.")
            return False
        start_iso = new_start_iso
        end_iso = new_end_iso

    event_body = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_iso},
        'end': {'dateTime': end_iso},
    }

    try:
        print(f"\nAdding event '{summary}' from {start_iso} to {end_iso}...")
        _ = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        # print(created_event)
        return True

    except HttpError as error:
        print(f"A API error occurred while adding event: {error}",
              file=sys.stderr)

        if hasattr(error, 'content'):
            try:
                error_details = json.loads(error.content)
                print(f"Error details: {json.dumps(error_details, indent=2)}",
                      file=sys.stderr)
            except json.JSONDecodeError:
                print(f"Error content: {error.content}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred while adding event: {e}",
              file=sys.stderr)
        return False
