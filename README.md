# mytaskie

A task management app built on google calendar.

# Setup

* GET a gemini api key from google ai studio()
* Get a CLIENT_SECRET and CLIENT_ID from google cloud console ()
* Add the following variables to a .env file:
    - GEMINI_API_KEY
    - GOOGLE_CLIENT_ID
    - GOOGLE_CLIENT_SECRET
    - USER_ID (For database queries)
* Install uv from the official website: https://docs.astral.sh/uv/getting-started/installation/
* run `uv sync` to install dependencies
* make the script executable by running `chmod +x mytaskie.py`

# Usage

```
./mytaskie.py -t "Code on the new feature on tomorrow between 10am and 12pm"

```
The task most include a description, a date, a time, and a priority level.
