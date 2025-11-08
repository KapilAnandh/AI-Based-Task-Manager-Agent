from fastapi import FastAPI
from pydantic import BaseModel
from src.agent import analyze_task
from src.db_manager import init_db, SessionLocal, add_task, update_task, list_tasks
from src.vector_store import add_or_update_vector, search

app = FastAPI(title="AI Task Manager Agent (Local & Free)")

# Initialize database once at startup
init_db()


class NLInput(BaseModel):
    """Natural language task input schema"""
    text: str


@app.post("/ingest")
def ingest_task(nl: NLInput):
    """Add a task from a natural language sentence."""
    data = analyze_task(nl.text)
    with SessionLocal() as s:
        obj = add_task(s, data)
        add_or_update_vector(
            obj.id,
            f"{obj.title}. {obj.description or ''}",
            {
                "category": obj.category,
                "priority": obj.priority,
                "status": obj.status,
            },
        )
        return {"id": obj.id, **data}


@app.get("/tasks")
def get_tasks(status: str | None = None, category: str | None = None, priority: str | None = None):
    """List all tasks, optionally filtered."""
    with SessionLocal() as s:
        items = list_tasks(s, {"status": status, "category": category, "priority": priority})
        return [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "priority": t.priority,
                "deadline": t.deadline,
                "due_date_iso": t.due_date_iso,
                "status": t.status,
            }
            for t in items
        ]


@app.get("/search")
def semantic_search(q: str, k: int = 5):
    """Semantic search using local embeddings."""
    results = search(q, k=k)
    return results


@app.patch("/tasks/{task_id}")
def patch_task(task_id: int, payload: dict):
    """Update a task's fields by ID."""
    with SessionLocal() as s:
        obj = update_task(s, task_id, payload)
        if not obj:
            return {"error": "Task not found"}

        add_or_update_vector(
            obj.id,
            f"{obj.title}. {obj.description or ''}",
            {
                "category": obj.category,
                "priority": obj.priority,
                "status": obj.status,
            },
        )
        return {"message": "Task updated successfully", "id": obj.id}