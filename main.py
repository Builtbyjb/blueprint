from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.oauth2 import id_token
import os
from redis import Redis
from taskie.auth import isAuth
from taskie.middleware import RateLimiter
from dotenv import load_dotenv
from taskie.taskie import my_taskie
from taskie.database import get_redis_client
from taskie.utils import generate_crypto_string
from taskie.auth import auth_config
from google.auth.transport import requests as google_requests
from taskie.logger import logger
from taskie.types import Task
import requests
from datetime import datetime, timedelta, timezone

load_dotenv()

redis_client: Redis = get_redis_client(os.getenv("REDIS_URL"))

# Google oauth2 configuration
oauth_config = auth_config()

app = FastAPI()
app.add_middleware(RateLimiter)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
async def health_check():
    return {"ping": "pong"}


@app.get("/")
async def Index(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id is not None:
        user_id = redis_client.get(str(session_id))
        name = redis_client.get(f"name:{user_id}")
        if isAuth(redis_client, str(user_id)):
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={"name":name}
            )
        else:
            return templates.TemplateResponse(
                request=request,
                name="auth.html",
                context={}
            )
    else:
        return templates.TemplateResponse(
            request=request,
            name="auth.html",
            context={}
        )


@app.post("/api/v1/task")
async def create_task(request: Request, task: Task) -> Response:
        session_id = request.cookies.get("session_id")
        if session_id is not None:
            try:
                user_id = redis_client.get(str(session_id))
            except:
                logger.error("Error getting or decoding user id")
                return Response(content="Internal server error", status_code=500)

            # Authenticate user before added task
            if isAuth(redis_client, str(user_id)):
                is_added = my_taskie(redis_client, task.task, user_id)
                if is_added:
                    return Response(content="Task created", status_code=200)
                else:
                    return Response(content="Unable to create task", status_code=400)
            else:
                logger.info("Unauthorized user adding task")
                return RedirectResponse(url="/", status_code=302)
        else:
            return RedirectResponse(url="/", status_code=302)


@app.get("/get-access")
async def get_access_token(request: Request) -> Response:
    # Generate the authorization URL
    authorization_url, state = oauth_config.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )

    response =  RedirectResponse(url=authorization_url, status_code=302)
    # Store the state in the session for CSRF protection
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    response.set_cookie(
        key="state",
        value=state,
        expires=expires,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
   )

    # Redirect to Google's authorization page
    return response


@app.get("/auth/google/callback")
async def google_auth_callback(request: Request) -> Response:
    # Verify state to prevent CSRF attacks
    state = request.query_params.get("state")
    stored_state = request.cookies.get("state")

    CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    if state is None or state != stored_state:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid state parameter. Possible CSRF attack."
        )

    # Exchange the authorization code for tokens
    try:
        code = request.query_params.get("code")
        payload = {
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URL"),
            "grant_type": "authorization_code"
        }

        token_response = requests.post(TOKEN_URL, data=payload)
        tokens = token_response.json()
        refresh_token = tokens.get("refresh_token")
        access_token = tokens.get("access_token")
        auth_id_token = tokens.get("id_token")
        if refresh_token is None:
            return Response(content="No refresh token", status_code=400)
    except:
        logger.error("Error getting authorization tokens")
        return Response(content="Error getting authorization tokens", status_code=400)

    # Verify the token and get user info
    try:
        user_info = id_token.verify_oauth2_token(
            auth_id_token,
            google_requests.Request(),
            CLIENT_ID
        )
    except:
        logger.error("Error verifing token and getting user info")
        return Response(content="Internal server error", status_code=500)

    # Save session cookie
    session_id = generate_crypto_string()

    email = str(user_info.get("email"))
    name =  str(user_info.get("given_name"))
    user_id = str(user_info.get("sub"))

     # Save user info
    try:
         redis_client.set(session_id, user_id, timedelta(days=20))
         redis_client.set(f"user_id:{user_id}", user_id)
         redis_client.set(f"name:{user_id}", name)
         redis_client.set(f"email:{user_id}", email)
         redis_client.set(f"access_token:{user_id}", access_token)
         redis_client.set(f"refresh_token:{user_id}", refresh_token)
    except:
        logger.error("Error setting session id and saving user info")
        return Response(content="Internal server error", status_code=500)

    response = RedirectResponse(url="/", status_code=302)  # Use 302 instead of default 307
    expires = datetime.now(timezone.utc) + timedelta(days=20)
    response.set_cookie(
        key="session_id",
        value=session_id,
        expires=expires,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
   )

    # Redirect to home page
    return response
