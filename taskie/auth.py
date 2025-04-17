import os
from redis.client import Redis
import requests
from google_auth_oauthlib.flow import Flow
from taskie.logger import logger
from typing import Optional

TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
TOKEN_REFRESH_URL = "https://oauth2.googleapis.com/token"
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    'https://www.googleapis.com/auth/calendar'
]

def auth_config() -> Flow:
    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URL = os.getenv("GOOGLE_REDIRECT_URL")
    SERVER_URL = os.getenv("SERVER_URL")

    client_config = {
        "web": {
            "project_id":"mytaskie-456602",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
             "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [REDIRECT_URL],
            "javascript_origins": [SERVER_URL]
        }
    }

    config = Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=REDIRECT_URL)
    return config


def verify_access_token(access_token: str) -> bool:
    """
        Verify google access token.
    """
    try:
        # Verify access token
        response = requests.get(
            TOKEN_INFO_URL,
            params={'access_token': access_token},
            timeout=10  # Add a timeout
        )
    except Exception as e:
        logger.error(f"Error verifying access token: {e}")
        return False

    if response.status_code == 200:
        return True
    else:
        return False


def refresh_access_token(refresh_token: str) -> tuple[Optional[str], bool]:
    """
        Refresh google access token.
    """
    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    try:
        response = requests.post(
            TOKEN_REFRESH_URL,
            data=payload,
            timeout=15
        )

        if response.status_code == 200:
            token_json = response.json()
            new_access_token = str(token_json["access_token"])
            return new_access_token, True
        else:
            logger.error(f"Token Refresh Error: {response.status_code} : {response.text}")
            return None, False

    except requests.exceptions.Timeout:
        logger.error("Token Refresh Error: Request timed out.")
        return None, False

    except requests.exceptions.RequestException as e:
        logger.error(f"Token Refresh Error: Network error ({e}).")
        return None, False


# Verify user
def isAuth(redis_client: Redis, user_id: str) -> bool:
    access_token =  str(redis_client.get(f"access_token:{user_id}"))
    if access_token is None:
        logger.info("No access token found")
        return False

    is_verified_token = verify_access_token(access_token)
    if not is_verified_token:
        # Refresh access token
        refresh_token = str(redis_client.get(f"refresh_token:{user_id}"))
        new_access_token, is_refreshed = refresh_access_token(refresh_token)
        if not is_refreshed or not new_access_token:
            return False
        try:
            redis_client.set(f"access_token:{user_id}", new_access_token)
            return True
        except Exception as e:
            logger.error(f"Error setting new access token: {e}")
            return False
    else:
        return True
