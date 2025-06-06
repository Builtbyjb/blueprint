from pydantic import BaseModel
from typing import List


# Google chat event
class Space(BaseModel):
  name: str
  type: str
  displayName: str


class Sender(BaseModel):
  name: str
  displayName: str
  email: str


class Thread(BaseModel): name: str


class Message(BaseModel):
  name: str
  createTime: str
  sender: Sender
  text: str
  thread: Thread


class Chat(BaseModel):
	type: str
	eventTime: str
	space: Space
	message: Message


class Tasks(BaseModel):
   task_id: str
   task: str
   is_completed: bool

class Projects(BaseModel): 
  project_name: str
  project_id: str
  tasks: List[Tasks]

