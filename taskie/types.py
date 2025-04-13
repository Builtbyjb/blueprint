from pydantic.main import BaseModel

# Google chat event
class Space(BaseModel):
    name: str
    type: str
    displayName: str

class Sender(BaseModel):
    name: str
    displayName: str
    email: str

class Thread(BaseModel):
    name: str

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


class Task(BaseModel):
    task: str
