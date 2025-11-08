import json
import httpx
import os
import time
from pydantic import BaseModel

# Default local Ollama endpoint
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")


class Ollama:
    """
    Local Ollama client wrapper for text generation and embeddings.
    Supports Qwen2.5, Gemma, and embedding models like nomic-embed-text.
    """

    def __init__(self, model: str):
        self.model = model
        self.client = httpx.Client(timeout=90)

    def generate(self, prompt: str, json_mode: bool = False) -> str:
        """
        Generate text (or JSON) from the given model.
        """
        payload = {"model": self.model, "prompt": prompt, "stream": False}
        if json_mode:
            payload["format"] = "json"

        try:
            response = self.client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

        except Exception as e:
            raise RuntimeError(f"❌ Ollama generate() failed: {e}") from e

    def embed(self, embed_model: str, text: str, retries: int = 3) -> list[float]:
        """
        Generate embeddings safely. Retries up to 3 times if empty or failed.
        """
        payload = {"model": embed_model, "input": text}

        for attempt in range(1, retries + 1):
            try:
                response = self.client.post(f"{OLLAMA_URL}/api/embeddings", json=payload)
                response.raise_for_status()
                data = response.json()

                # Handle both key formats
                emb = data.get("embedding") or (
                    data.get("embeddings")[0] if "embeddings" in data else None
                )

                if emb and isinstance(emb, list) and len(emb) > 0:
                    return emb

                print(f"[yellow]⚠️ Empty embedding returned (attempt {attempt}) — retrying...[/yellow]")
                time.sleep(1)

            except Exception as e:
                print(f"[red]❌ Embedding failed (attempt {attempt}):[/red] {e}")
                time.sleep(1)

        # Final fallback: return a dummy vector instead of crashing
        print("[red]⚠️ Ollama failed to generate a valid embedding. Returning fallback vector.[/red]")
        return [0.0] * 768  # typical embedding size
