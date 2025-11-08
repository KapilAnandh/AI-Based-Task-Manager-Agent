import os
import chromadb
from chromadb.config import Settings
from models.ollama_client import Ollama

# =========================================================
# CONFIGURATION
# =========================================================

# Disable Chroma telemetry (for local privacy)
os.environ["ANONYMIZED_TELEMETRY"] = "false"

CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:1.5b")

# Initialize Ollama client (for embeddings)
ollama = Ollama(model=LLM_MODEL)

# Create Chroma persistent client + collection
def get_vector_client():
    """
    Returns a persistent Chroma client connected to local 'data/chroma'.
    Used by add/search/delete to keep consistency.
    """
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(
        path=CHROMA_DIR,
        settings=Settings(allow_reset=True)
    )
    return client


# Single shared collection instance
_client = get_vector_client()
collection = _client.get_or_create_collection("tasks")


# =========================================================
# EMBEDDING UTILITIES
# =========================================================

def embed_text(text: str) -> list[float]:
    """
    Generate embeddings for text via Ollama's embedding model.
    Provides a safe fallback if embedding is empty.
    """
    if not text or not text.strip():
        raise ValueError("❌ Cannot embed empty text.")

    emb = ollama.embed(EMBED_MODEL, text)

    # Handle empty embeddings gracefully
    if not emb or len(emb) == 0:
        print(f"[yellow]⚠️ Empty embedding detected for text: {text[:50]}... using fallback vector.[/yellow]")
        emb = [0.0] * 768  # fallback vector
    elif isinstance(emb[0], list):  # flatten nested embeddings if needed
        emb = emb[0]

    return emb


# =========================================================
# UPSERT (ADD OR UPDATE)
# =========================================================

def add_or_update_vector(task_id: int, text: str, metadata: dict):
    """
    Add or update a task vector in Chroma collection.
    """
    try:
        emb = embed_text(text)
        collection.upsert(
            ids=[str(task_id)],
            embeddings=[emb],
            metadatas=[metadata],
            documents=[text],
        )
        print(f"[green]✅ Vector stored for Task ID {task_id}[/green]")
    except Exception as e:
        print(f"[yellow]⚠️ Skipped vector embedding for Task {task_id} due to error:[/yellow] {e}")


# =========================================================
# SEARCH
# =========================================================

def search(query: str, k: int = 5):
    """
    Perform semantic search on the task collection using embeddings.
    """
    q_emb = embed_text(query)
    return collection.query(query_embeddings=[q_emb], n_results=k)


# =========================================================
# DELETE UTILITIES
# =========================================================

def delete_vector(task_id: int):
    """
    Delete a specific task vector by ID.
    """
    try:
        collection.delete(ids=[str(task_id)])
        print(f"[red]🗑️ Deleted vector for Task ID {task_id}[/red]")
    except Exception as e:
        print(f"[yellow]⚠️ Could not delete vector for Task ID {task_id}: {e}[/yellow]")


def clear_all_vectors():
    """
    Safely delete the entire Chroma vector store (used in --all deletes).
    Handles Windows file locks and ensures client is closed.
    """
    import shutil, time

    print("[yellow]⚙️ Closing Chroma client before deletion...[/yellow]")
    try:
        _client._system.stop()
    except Exception as e:
        print(f"[yellow]⚠️ Warning while closing Chroma client:[/yellow] {e}")

    # Try deleting folder safely (handles Windows file lock)
    for attempt in range(3):
        try:
            if os.path.exists(CHROMA_DIR):
                shutil.rmtree(CHROMA_DIR)
            print("[red]🧹 Cleared all embeddings from Chroma vector store.[/red]")
            return True
        except PermissionError:
            print(f"[yellow]⚠️ Chroma files locked (attempt {attempt + 1}/3)... retrying[/yellow]")
            time.sleep(1)

    print("[red]❌ Failed to delete Chroma folder after retries.[/red]")
    return False


# =========================================================
# EXPORTS
# =========================================================

__all__ = [
    "get_vector_client",
    "embed_text",
    "add_or_update_vector",
    "search",
    "delete_vector",
    "clear_all_vectors",
]
