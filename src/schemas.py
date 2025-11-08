from pydantic import BaseModel
from typing import Optional


class TaskIn(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    priority: str
    deadline: Optional[str] = None
    due_date_iso: Optional[str] = None
    status: str = "Pending"


class Task(TaskIn):
    id: int