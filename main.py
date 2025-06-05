from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from google.oauth2 import id_token
import os
from redis import Redis
from blueprint.auth import isAuth
from blueprint.middleware import RateLimiter
from dotenv import load_dotenv
from blueprint.blueprint import blueprint
from database.redis.redis import get_redis_client
from blueprint.utils import generate_crypto_string
from blueprint.auth import auth_config
from google.auth.transport import requests as google_requests
from blueprint.logger import log
from blueprint.types import Task
import requests
from datetime import datetime, timedelta, timezone
from database.sqlite.sqlite import sqlite
from pydantic import BaseModel
from typing import Union
import uvicorn

load_dotenv()

redis_client: Redis = get_redis_client(os.getenv("REDIS_URL"))
dbCur, dbCon = sqlite()

# Google oauth2 configuration
oauth_config = auth_config()

app = FastAPI()
app.add_middleware(RateLimiter)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/health")
async def health_check(): return {"ping": "pong"}


@app.get("/")
async def Index(request: Request):
  session_id = request.cookies.get("session_id")
  if session_id is not None:
    user_id = redis_client.get(str(session_id)) # Potential failure point
    tasks= []
    try:
      # TODO: add a task schema to sqlite so i want have to use index to identify table values
      t = dbCur.execute("SELECT * FROM tasks WHERE user_id=?", (user_id,))
      tasks = t.fetchall()
    except Exception as e:
      log.error(f"Error fetching tasks: {e}")
      return Response(content="Internal server error", status_code=500)

    name = redis_client.get(f"name:{user_id}")
    if isAuth(redis_client, str(user_id)):
      return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={ "name":name, "tasks":tasks }
      )
    else:
      return templates.TemplateResponse( request=request, name="auth.html", context={})
  else:
    return templates.TemplateResponse( request=request, name="auth.html", context={})


@app.post("/api/v1/task", response_model=None)
async def create_task(request: Request, task: Task) -> Union[JSONResponse, RedirectResponse]:
  """
  Creates a new task. Adds the task to google calendar or a database,
  depending on if the tasks contains a time reference or not.
  """
  session_id = request.cookies.get("session_id")
  if session_id is not None:
    try: user_id = redis_client.get(str(session_id))
    except:
      log.error("Error getting or decoding user id")
      return JSONResponse( content={"error":"Internal server error"}, status_code=500)
    # Authenticate user before added task
    if isAuth(redis_client, str(user_id)):
      is_added, task_id = blueprint(redis_client, dbCur, dbCon, task.task, user_id)
      if is_added:
        return JSONResponse(
          content={ "message":"Task created", "taskID": task_id },
          status_code=200
        )
      else:
        return JSONResponse( content={"error":"Unable to create task"}, status_code=400)
    else:
      log.info("Unauthorized user adding task")
      return RedirectResponse(url="/", status_code=302)
  else: return RedirectResponse(url="/", status_code=302)


@app.delete("/api/v1/tasks/{task_id}")
async def delete_task(task_id: str) -> JSONResponse:
  """
  Delete tasks from the database
  """
  try:
    dbCur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    dbCon.commit()
    return JSONResponse( content={"message":"Task deleted"}, status_code=200)
  except Exception as e:
    log.error(f"Error deleting task: {e}")
    return JSONResponse( content={"error":"Unable to delete task"}, status_code=500)


class TaskUpdate(BaseModel): is_completed: int


@app.put("/api/v1/tasks/{task_id}")
async def update_task(task_id: str, task: TaskUpdate) -> JSONResponse:
  """
  Updates a task added to database, "is_completed" value.
  """
  try:
    dbCur.execute("UPDATE tasks SET is_completed = ? WHERE id = ?", (task.is_completed, task_id))
    dbCon.commit()
    return JSONResponse( content={"message":"Task updated"}, status_code=200)
  except Exception as e:
    print(f"Error updating task: {e}")
    return JSONResponse( content={"error":"Unable to update task"}, status_code=500)


@app.get("/get-access")
async def get_access_token(request: Request) -> Response:
  """
  Starts google oauth flow to grant "Blueprint" access to
  the users google calendar service.
  """
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
  """
  Handles google callbacks. Get access token, refresh token and user information
  from google and saves them in a redis database
  """
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
    log.error("Error getting authorization tokens")
    return Response(content="Error getting authorization tokens", status_code=400)

  # Verify the token and get user info
  try:
    user_info = id_token.verify_oauth2_token(
      auth_id_token,
      google_requests.Request(),
      CLIENT_ID
    )
  except:
    log.error("Error verifying token and getting user info")
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
    log.error("Error setting session id and saving user info")
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


if __name__ == "__main__":
  uvicorn.run("main:app", host="127.0.0.1", port=3000, log_level="info")