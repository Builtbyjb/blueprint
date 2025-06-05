import datetime
import pytz

DEFAULT_EVENT_DURATION_MINUTES = 60

def generate_task_prompt(task):
  local_tz = pytz.timezone("Canada/Eastern")

  now_local = datetime.datetime.now(local_tz)
  now_iso = now_local.isoformat()

  prompt = f"""
  Analyze the following task description and extract the details needed to
  create a Google Calendar event. Assume the current time is {now_iso}
  in the {local_tz} timezone unless otherwise specified in the task.

  Task: "{task}"

  Provide the output ONLY as a JSON object with the following keys:
  - "summary": A concise title for the event (string).
  - "start_time": The start date and time in ISO 8601 format
  (YYYY-MM-DDTHH:MM:SS±HH:MM). Infer the date if only
  time is mentioned (assume today or the nearest future date). Include the
  correct timezone offset.
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
  If the task contains a number without a time reference like (AM, PM, hours, minutes, etc.), return:
  {{
      "info": "Task contains a number without a time reference",
  }}.
  If no time information is present return:
  {{
      "info": "Task was not assigned a time frame",
  }}.
  Ensure the start and end times are valid ISO 8601 strings including timezone offset derived from the context or
  the user's explicit mention.
  """

  return prompt
