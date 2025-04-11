#!/usr/bin/env python3


import argparse
import requests
import sys
from dotenv import load_dotenv
from google import genai
import datetime
import pytz
import os
import sqlite3
import tzlocal
import json
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


DEFAULT_EVENT_DURATION_MINUTES = 60
FIND_NEXT_SLOT_INCREMENT_MINUTES = 30
FIND_NEXT_SLOT_MAX_HOURS = 4
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
TOKEN_REFRESH_URL = "https://oauth2.googleapis.com/token"

# Create a sqlite3 database engine
def database():
    dbCon = sqlite3.connect("db.sqlite3")
    db = dbCon.cursor()
    db.execute("CREATE TABLE IF NOT EXISTS user(id, refresh_token, access_token)")
    return db, dbCon


def generate_prompt(task):
    try:
        # Determine local timezone (important for Gemini context)
        local_tz = tzlocal.get_localzone()
        local_tz_name = str(local_tz)
        print(f"Using local timezone: {local_tz_name}")
    except Exception as tz_err:
        print(f"Warning: Could not reliably determine local timezone ({tz_err}). Gemini might use UTC or make assumptions.", file=sys.stderr)
        # Fallback or prompt user if needed - for now, proceed cautiously
        local_tz = pytz.utc # Fallback to UTC

    now_local = datetime.datetime.now(local_tz)
    now_iso = now_local.isoformat()

    prompt = f"""
    Analyze the following task description and extract the details needed to create a Google Calendar event.
    Assume the current time is {now_iso} in the {local_tz} timezone unless otherwise specified in the task.

    Task: "{task}"

    Provide the output ONLY as a JSON object with the following keys:
    - "summary": A concise title for the event (string).
    - "start_time": The start date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS±HH:MM). Infer the date if only
    time is mentioned (assume today or the nearest future date). Include the correct timezone offset.
    - "end_time": The end date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS±HH:MM). If only a start time or
    duration is mentioned, assume a default duration of {DEFAULT_EVENT_DURATION_MINUTES} minutes. Ensure the end
    time includes the correct timezone offset.
    - "description": A detailed description for the event body (string, can be same as task if simple).

    Example Input Task: "Schedule haircut tomorrow at 2 PM for about an hour"
    Example Output JSON (assuming today is 2023-10-26 and local timezone is -07:00):
    {{
      "summary": "Haircut",
      "start_time": "2023-10-27T14:00:00-07:00",
      "end_time": "2023-10-27T15:00:00-07:00",
      "description": "Schedule haircut tomorrow at 2 PM for about an hour"
    }}

    If the task is ambiguous about time, make a reasonable guess (e.g., 'meeting this afternoon' could be 3 PM today).
    If no time information is present *at all*, return an error indicator.
    Ensure the start and end times are valid ISO 8601 strings including timezone offset derived from the context or
    the user's explicit mention.
    """

    return prompt


# Verify user
def isAuth(db, dbCon):
    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    USER_ID = os.getenv("USER_ID")

    res = db.execute("SELECT * FROM user WHERE id=?", (USER_ID,))
    user = res.fetchone()

    if user is None:
        print("No user found")
        return False

    refresh_token = user[1]
    access_token = user[2]

    if access_token == "":
        print("No access token found")
        return False

    try:
        response = requests.get(
            TOKEN_INFO_URL,
            params={'access_token': access_token},
            timeout=10 # Add a timeout
        )
        if response.status_code == 200:
            return True
        else:
            # Try refreshing the token
            payload = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }

            try:
                response = requests.post(TOKEN_REFRESH_URL, data=payload, timeout=15)
                if response.status_code == 200:
                    token_json = response.json()
                    new_refresh_token = token_json["refresh_token"]
                    new_access_token = token_json["access_token"]

                    # Save new access_token and refresh_token
                    sql = "UPDATE user SET refresh_token=? access_token=? WHERE id=?"
                    values = (new_refresh_token, new_access_token, USER_ID)
                    db.execute(sql, values)
                    dbCon.commit()

                    return True
            except requests.exceptions.Timeout:
                  print("Token Refresh Error: Request timed out.")
                  return False
            except requests.exceptions.RequestException as e:
                print(f"Token Refresh Error: Network error ({e}).")
                return False
    except requests.exceptions.Timeout:
        print("Token Verification Error: Request timed out.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Token Verification Error: Network error ({e}).")
        return False
    return True


# Authenticate user
def authenicate(db, dbCon):
    USER_ID = os.getenv("USER_ID")
    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    client_config = {
            "installed": {
                "project_id":"gen-lang-client-0805862153",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
             }
        }

    flow = InstalledAppFlow.from_client_config(
            client_config, CALENDAR_SCOPES)

    try:
        creds = flow.run_local_server(port=0)
        refresh_token = creds.refresh_token
        access_token = creds.token

        sql = "INSERT INTO user (id, refresh_token, access_token) VALUES(?, ?, ?)"
        values = (USER_ID, refresh_token, access_token)
        db.execute(sql, values)
        dbCon.commit()

        return True
    except OSError:
         print("Could not start local server for auth.")
         return False
    except Exception as e:
         print(f"An unexpected error occurred during authentication: {e}")
         return False


def gemini_response(prompt):
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


def is_slot_free(service, start_time_iso, end_time_iso, calendar_id='primary'):
    """Checks if a time slot is free using the freebusy API."""
    print(f"Checking availability from {start_time_iso} to {end_time_iso}...")
    try:
        # Use timezone from start_time string for the query
        tz_info = dateutil_parser.isoparse(start_time_iso).tzinfo
        tz_str = str(tz_info) if tz_info else 'UTC' # Default to UTC if no tz info

        freebusy_query = {
            "timeMin": start_time_iso,
            "timeMax": end_time_iso,
            "timeZone": tz_str,
            "items": [{"id": calendar_id}]
        }
        results = service.freebusy().query(body=freebusy_query).execute()
        calendar_busy_times = results.get('calendars', {}).get(calendar_id, {}).get('busy', [])

        if not calendar_busy_times:
            print("Slot is free.")
            return True
        else:
            # Optional: Check if the busy interval *exactly* overlaps.
            # For simplicity, any overlap is considered busy here.
            print(f"Slot is busy. Conflicts: {calendar_busy_times}")
            return False

    except HttpError as error:
        print(f"An API error occurred during free/busy check: {error}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred during free/busy check: {e}", file=sys.stderr)
        return False

def find_next_free_slot(service, original_start_dt, original_end_dt, calendar_id='primary'):
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
def add_task(db, task):
    prompt = generate_prompt(task)
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
         print(f"ERROR: Could not parse date/time from Gemini: {e}", file=sys.stderr)
         return False

    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    USER_ID = os.getenv("USER_ID")

    res = db.execute("SELECT * FROM user WHERE id=?", (USER_ID,))
    user = res.fetchone()
    if user is None:
        return False

    refresh_token = user[1]
    access_token = user[2]

    credentials = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )

    try:
        service = build('calendar', 'v3', credentials=credentials)
    except Exception as build_error:
         print(f"Failed to build Google Calendar service client: {build_error}", file=sys.stderr)
         sys.exit(1)

    if not is_slot_free(service, start_iso, end_iso, calendar_id):
        new_start_iso, new_end_iso = find_next_free_slot(service, start_dt, end_dt, calendar_id)
        if not new_start_iso:
            print("Failed to find an alternative slot. Event not added.", file=sys.stderr)
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
        print(f"An API error occurred while adding event: {error}", file=sys.stderr)

        if hasattr(error, 'content'):
            try:
                error_details = json.loads(error.content)
                print(f"Error details: {json.dumps(error_details, indent=2)}", file=sys.stderr)
            except json.JSONDecodeError:
                print(f"Error content: {error.content}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred while adding event: {e}", file=sys.stderr)
        return False


def main():
    load_dotenv()

    # Create database engine
    db, dbCon = database()

    parser = argparse.ArgumentParser(description='MyTaskie CLI')
    parser.add_argument("-t", "--task", dest="task", help='Task description')
    args = parser.parse_args()

    if args.task:
       if isAuth(db, dbCon):
           add_task(db, args.task)
       else:
           print("User not authenticated. Begin authentication flow")
           auth_flow_completed = authenicate(db, dbCon)
           if auth_flow_completed:
               add_task(db, args.task)
           sys.exit(1)
    else:
        print("No task provided, read the README.md file for more information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
