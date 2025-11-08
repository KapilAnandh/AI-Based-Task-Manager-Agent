import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_PATH = "./data/tasks.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # Ensure /data exists

DB_URL = os.getenv("DB_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ============================================================
# ORM MODEL
# ============================================================

class TaskORM(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    deadline = Column(String, nullable=True)
    due_date_iso = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Pending")

# Backward-compatible alias (so you can import Task directly)
Task = TaskORM


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)


# ============================================================
# CRUD OPERATIONS
# ============================================================

def add_task(session, task: dict) -> TaskORM:
    """Add a new task to the database."""
    obj = TaskORM(**task)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def update_task(session, task_id: int, updates: dict) -> TaskORM | None:
    """Update an existing task."""
    obj = session.get(TaskORM, task_id)
    if not obj:
        return None
    for k, v in updates.items():
        setattr(obj, k, v)
    session.commit()
    session.refresh(obj)
    return obj


def list_tasks(session, filters: dict | None = None):
    """List tasks with optional filters."""
    q = session.query(TaskORM)
    if filters:
        for k, v in filters.items():
            if v is None:
                continue
            if hasattr(TaskORM, k):
                q = q.filter(getattr(TaskORM, k) == v)
    return q.order_by(TaskORM.id.desc()).all()


# ============================================================
# DELETE OPERATIONS
# ============================================================

def delete_task(session, task_id: int) -> bool:
    """Delete a single task by ID."""
    obj = session.get(TaskORM, task_id)
    if not obj:
        return False
    session.delete(obj)
    session.commit()
    return True


def delete_all_tasks(session) -> int:
    """Delete all tasks from the database."""
    count = session.query(TaskORM).delete()
    session.commit()
    return count


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "TaskORM",
    "Task",
    "SessionLocal",
    "init_db",
    "add_task",
    "update_task",
    "list_tasks",
    "delete_task",
    "delete_all_tasks",
]