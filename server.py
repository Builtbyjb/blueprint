from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic.main import BaseModel
# import uvicorn
# import os
from middleware import RateLimiter
from dotenv import load_dotenv
from mytaskie import my_taskie

load_dotenv()

app = FastAPI()
app.add_middleware(RateLimiter)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


class Task(BaseModel):
    task: str


@app.get("/")
async def health_check(request: Request):
    return {"ping": "pong"}


@app.post("/api/v1/task")
async def create_task(request: Request, task: Task):
    # my_taskie(task.task)
    print(task.task)
    return {"message": "Task created"}
