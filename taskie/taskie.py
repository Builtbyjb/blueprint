from google import genai
from redis import Redis
import os
import json
from taskie.logger import logger
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from taskie.prompt import generate_task_prompt
from pydantic import BaseModel
from typing import Optional
from taskie.utils import generate_crypto_string
from taskie.auth import verify_access_token, refresh_access_token


DEFAULT_EVENT_DURATION_MINUTES = 60
FIND_NEXT_SLOT_INCREMENT_MINUTES = 30
FIND_NEXT_SLOT_MAX_HOURS = 4
TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
TOKEN_REFRESH_URL = "https://oauth2.googleapis.com/token"


class SanitizedResponse(BaseModel):
    summary: str
    start_time: str
    end_time: str
    description: str

    # Get class attributes
    def __getitem__(self, key):
        return getattr(self, key)


def gemini_response(prompt: str):
    """
    returns a json object containing the "SanitizedResponse type values" or
    a dict with a key of "info" if a time frame for the task is not specified
    """
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
    """
    returns a type of SanitizedResponse or a dict with a "info" key
    """
    cleaned_response_text = response.text.strip().strip('`').strip()
    if cleaned_response_text.lower().startswith("json"):
        cleaned_response_text = cleaned_response_text[4:].strip()

    logger.info(f"Gemini Raw Response:\n{cleaned_response_text}")
    sanitized_response = json.loads(cleaned_response_text)
    return sanitized_response


def verify_response_values(sanitized_response) -> Optional[SanitizedResponse]:
    """
    Verify gemini response json object, ensures it contains all the values
    needed to create a google calendar event
    """
    if sanitized_response.get("info"):
        return None

    if not all(k in sanitized_response for k in ["summary", "start_time", "end_time", "description"]):
        raise ValueError("Gemini response missing required keys.")

    if not sanitized_response.get("summary") \
        or not sanitized_response.get("start_time")  \
        or not sanitized_response.get("end_time"):
        raise ValueError("Gemini response has empty essential values (summary, start_time, end_time).")

    try:
        dateutil_parser.isoparse(sanitized_response["start_time"])
        dateutil_parser.isoparse(sanitized_response["end_time"])
    except ValueError as e:
        raise ValueError(f"Gemini returned invalid ISO 8601 date format: {e}")

    return sanitized_response


def is_slot_free(service, start_time_iso, end_time_iso, calendar_id='primary') -> bool:
    """Checks if a time slot is free using the freebusy API."""
    logger.info(f"Checking availability from {start_time_iso} to {end_time_iso}...")
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
            logger.error(f"Error executing free busy query {e}")
            # TODO: Logout user is this fails or prompt the the user to authenticate
            return False

        calendar_busy_times = results.get('calendars', {}) \
            .get(calendar_id, {}) \
            .get('busy', [])

        if not calendar_busy_times:
            logger.info("Slot is free.")
            return True
        else:
            logger.info(f"Slot is busy. Conflicts: {calendar_busy_times}")
            return False

    except HttpError as e:
        logger.error(f"An API error occurred during free/busy check: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during free/busy check: {e}")
        return False


def find_next_free_slot(
        service, original_start_dt, original_end_dt, calendar_id='primary'):
    """Finds the next available time slot of the same duration."""
    duration = original_end_dt - original_start_dt
    # Start searching right after the originally proposed end time,
    # ensuring we maintain the original timezone info.
    current_start_dt = original_end_dt
    search_limit_dt = original_start_dt + relativedelta(hours=FIND_NEXT_SLOT_MAX_HOURS)

    logger.info(f"\nSearching for the next free slot with duration {duration}...")

    while current_start_dt < search_limit_dt:
        current_end_dt = current_start_dt + duration
        start_iso = current_start_dt.isoformat()
        end_iso = current_end_dt.isoformat()

        if is_slot_free(service, start_iso, end_iso, calendar_id):
            logger.info(f"Found next available slot: {start_iso} to {end_iso}")
            return start_iso, end_iso

        current_start_dt += relativedelta(minutes=FIND_NEXT_SLOT_INCREMENT_MINUTES)

    logger.info(f"Could not find a free slot within the next {FIND_NEXT_SLOT_MAX_HOURS} hours.")
    return None, None


def create_calendar_service(redis_client: Redis, user_id: str):
    """
        Create a google calendar service.
        Returns a google calender service or None, if the service
        was not successfully created.
    """
    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    access_token = str(redis_client.get(f"access_token:{user_id}"))
    refresh_token = str(redis_client.get(f"refresh_token:{user_id}"))

    if not access_token or not refresh_token:
        logger.error("Missing access or refresh token")
        return None

    # Verify access token
    is_verified = verify_access_token(access_token)
    if not is_verified:
        # Refresh access token
        new_access_token, is_refreshed = refresh_access_token(refresh_token)
        if not new_access_token or not is_refreshed:
            logger.error(f"Failed to refresh access token for user {user_id}")
            return None
        else:
            try:
                # Save new access token to Redis
                redis_client.set(f"access_token:{user_id}", new_access_token)
            except Exception as e:
                logger.error(f"Failed to update access token in Redis: {e}")
                return None

    credentials = Credentials(
        token=access_token,
        token_uri=TOKEN_REFRESH_URL,
        refresh_token=refresh_token,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    )

    try:
        service = build('calendar', 'v3', credentials=credentials)
    except Exception as e:
        logger.error(f"Failed to build Google Calendar service client: {e}")
        return None
    return service


def add_calendar_event(
    sanitized_response: SanitizedResponse,
    redis_client: Redis,
    user_id: str,
    calendar_id="primary") -> bool:
    # print(sanitized_response)
    summary = sanitized_response["summary"]
    start_iso = sanitized_response["start_time"]
    end_iso = sanitized_response["end_time"]
    description = sanitized_response["description"]

    try:
        start_dt = dateutil_parser.isoparse(start_iso)
        end_dt = dateutil_parser.isoparse(end_iso)
    except ValueError as e:
        logger.error(f"ERROR: Could not parse date/time from Gemini: {e}")
        return False

    service = create_calendar_service(redis_client, user_id)
    if service is None:
        return False

    if not is_slot_free(service, start_iso, end_iso, calendar_id):
        new_start_iso, new_end_iso = find_next_free_slot(
            service,
            start_dt,
            end_dt,
            calendar_id)
        if not new_start_iso:
            logger.error("Failed to find an alternative slot. Event not added.")
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
        logger.info(f"\nAdding event '{summary}' from {start_iso} to {end_iso}...")
        _ = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        # print(created_event)
        return True

    except HttpError as e:
        logger.error(f"A API error occurred while adding event: {e}")

        if hasattr(e, 'content'):
            try:
                error_details = json.loads(e.content)
                logger.error(f"Error details: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                logger.error(f"Error content: {e.content}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while adding event: {e}")
        return False
    return True

# Add task to google calender
def my_taskie(redis_client, dbCur, dbCon, task, user_id) -> tuple[bool, str]:
    prompt = generate_task_prompt(task)
    response = gemini_response(prompt)
    sanitized_response = sanitize_gemini_response(response)
    verified_response = verify_response_values(sanitized_response)

    if verified_response is None:
        # Save task to and sqlite database and return the id
        task_id = generate_crypto_string()
        try:
            dbCur.execute(
                "INSERT INTO tasks (id, user_id, task, is_completed) VALUES (?, ?, ?, ?)",
                (task_id, user_id, task, False)
            )
            dbCon.commit()
            return True, task_id
        except Exception as e:
            logger.error(f"An unexpected error occurred while saving task to database: {e}")
            return False, ""
    else:
        # Add task to google calender
        is_added = add_calendar_event(sanitized_response, redis_client, user_id)
        return is_added, ""
