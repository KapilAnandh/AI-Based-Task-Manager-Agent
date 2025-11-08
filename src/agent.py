import os
import json
import re
from models.ollama_client import Ollama
from utils.prompt_templates import SYSTEM_INSTRUCTIONS, USER_TEMPLATE, TASK_JSON_SCHEMA
from utils.parser import extract_and_validate_json, JSONParseError

# Load model name from environment (default Qwen2.5)
MODEL = os.getenv("LLM_MODEL", "qwen2.5:1.5b")
ollama = Ollama(model=MODEL)

# Regex to extract JSON from mixed text
CLEAN_JSON_RE = re.compile(r"\{[\s\S]*\}")


def clean_json_output(raw_text: str) -> str:
    """
    Extract first {...} block and remove markdown/code fences.
    """
    if "```" in raw_text:
        raw_text = raw_text.replace("```json", "").replace("```", "")
    match = CLEAN_JSON_RE.search(raw_text)
    if match:
        return match.group(0)
    return raw_text


def normalize_task_data(data: dict) -> dict:
    """
    Fix common model output mistakes (like 'Normal' priority, missing status, capitalization).
    """
    # Default status if missing
    if "status" not in data or not data["status"]:
        data["status"] = "Pending"

    # Map 'Normal' → 'Medium'
    if data.get("priority", "").lower() == "normal":
        data["priority"] = "Medium"

    # Ensure proper capitalization of category
    if "category" in data and isinstance(data["category"], str):
        data["category"] = data["category"].capitalize()

    # Fill missing description field
    if "description" not in data:
        data["description"] = None

    return data


def analyze_task(task_input: str) -> dict:
    """
    Query the local LLM (via Ollama) to analyze a natural language task
    and return structured JSON following TASK_JSON_SCHEMA.
    """
    system_prompt = f"{SYSTEM_INSTRUCTIONS}\n\n"
    user_prompt = USER_TEMPLATE.format(task_input=task_input)
    prompt = system_prompt + user_prompt

    for attempt in range(3):
        print(f"[Attempt {attempt + 1}] Asking model...")

        try:
            out = ollama.generate(prompt, json_mode=False)
        except Exception as e:
            print(f"[red] LLM call failed:[/red] {e}")
            continue

        cleaned = clean_json_output(out)

        try:
            data = extract_and_validate_json(cleaned, TASK_JSON_SCHEMA)
            data = normalize_task_data(data)
            print("[green] Parsed JSON successfully![/green]")
            return data

        except JSONParseError as e:
            print(f"[yellow] JSON parse failed:[/yellow] {e}")
            prompt += (
                "\nThe last response was invalid. "
                "Please output only a valid JSON object following the schema. "
                "No explanations, no markdown, and ensure all required fields are included."
            )

    raise ValueError("Model could not produce valid JSON after multiple retries.")
