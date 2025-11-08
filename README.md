A **fully local**, **privacy-first** AI agent that converts natural language tasks into structured, searchable, and updatable entries using **Ollama**, **Chroma vector DB**, **FastAPI**, and **Rich CLI**.
No OpenAI. No cloud. No API keys.
---

## Features
- **Natural Language → JSON** via `qwen2.5:1.5b` + `nomic-embed-text`
- **Semantic search** with local embeddings
- **Persistent storage**: SQLite + Chroma
- **REST API** (`/ingest`, `/search`, `/patch`)
- **Rich CLI** with filtering, tables, and safe delete
- **Docker-ready** with auto Ollama setup
- **Windows-safe** file handling
---

## Tech Stack

| Component       | Technology                          |
|----------------|-------------------------------------|
| LLM & Embeddings | [Ollama](https://ollama.com) (`qwen2.5:1.5b`, `nomic-embed-text`) |
| Vector DB       | [Chroma](https://www.trychroma.com) (persistent) |
| API             | FastAPI + Pydantic                  |
| CLI             | Click + Rich                        |
| ORM             | SQLAlchemy                          |
| Validation      | JSON Schema + `jsonschema`          |

---
## Project Structure
/src          → Core logic (agent, API, DB, CLI)
/models       → Ollama client wrapper
/utils        → Prompt templates, JSON parser
/data         → SQLite DB + Chroma vector store
Dockerfile    → Full container setup
.env.example  → Configuration template

## Quick Start
### 1. Clone & Setup
git clone https://github.com/KapilAnandh/AI-Based-Task-Manager-Agent.git
cd AI-Based-Task-Manager-Agent
cp .env.example .env

### 2. Install & Run Locally
pip install -r requirements.txt
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
python src/main.py add "Finish report by tomorrow" --due 2025-11-10

### 3. Or Use Docker (Recommended)
docker build -t ai-task-manager .
docker run -p 8000:8000 -p 11434:11434 -v $(pwd)/data:/app/data ai-task-manager
API: http://localhost:8000/docs
Ollama: http://localhost:11434

### CLI Usage:
# Add task
python src/main.py add "Buy milk high priority" --due 2025-11-09
# List tasks
python src/main.py list --priority High
# Semantic search
python src/main.py find --q "work deadlines"
# Update
python src/main.py update 1 --status Done

### API Endpoints:
Method,Endpoint,Description
POST,/ingest,Add task from text
GET,/tasks,List with filters
GET,/search?q=...,Semantic search

### Best Practices Implemented
* Modular, typed, reusable code
* Environment-based config (.env)
* JSON schema validation
* Retry logic + fallbacks
* Thread-safe DB sessions
* Safe Windows file deletion
* Production-ready logging
* PATCH,/tasks/{id},Update task

### Cheatsheet:
| Action              | Command                                             | Notes                            |
| ------------------- | --------------------------------------------------- | -------------------------------- |
| ➕ Add Task          | `python -m src.main add "Task description"`         | Creates a new AI-parsed task     |
| ➕ Add with Due Date | `python -m src.main add "Task" --due 2025-11-12`    | Adds custom due date             |
| 📋 List All         | `python -m src.main list`                           | Show all tasks                   |
| 📂 Filter           | `python -m src.main list --category Work`           | Filter by any field              |
| ✏️ Update           | `python -m src.main update 1 --status Done`         | Update one or more fields        |
| 🔍 Find (Semantic)  | `python -m src.main find --q "review presentation"` | Searches using vector embeddings |
| 🗑️ Delete          | `python -m src.main delete 2`                       | Delete a specific task           |
| 💣 Delete All       | `python -m src.main delete --all`                   | Clears DB + embeddings           |


### Video Walkthrough
Link : 
