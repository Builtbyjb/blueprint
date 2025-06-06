from sqlmodel import Field, SQLModel
from typing import Optional


class Task(SQLModel, table=True):
  __tablename__ = "tasks"
  id: str = Field(primary_key=True)
  task: str
  project_id: Optional[str] = None
  todo: bool = Field(default=False)
  is_completed: bool


class Project(SQLModel, table=True):
  __tablename__ = "projects"
  id: str
  user_id: str
  name: str