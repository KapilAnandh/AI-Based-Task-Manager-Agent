TASK_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": ["string", "null"]},
        "category": {
            "type": "string",
            "enum": [
                "Work", "Personal", "Study", "Health", "Finance", "Errand", "Other"
            ]
        },
        "priority": {
            "type": "string",
            "enum": ["High", "Medium", "Low", "Normal"]
        },
        "deadline": {"type": ["string", "null"]},
        "due_date_iso": {"type": ["string", "null"]},
        "status": {
            "type": "string",
            "enum": ["Pending", "In-Progress", "Done", "To Do"]
        }
    },
    "required": ["title", "category", "priority"],
    "additionalProperties": False
}

SYSTEM_INSTRUCTIONS = (
    "You are an AI Task Manager agent. "
    "Your job is to extract a structured JSON object from a natural language task. "
    "Each JSON object should include: "
    "title, description, category (Work, Personal, Study, Health, Finance, Errand, Other), "
    "priority (High, Medium, Low), deadline (string or null), due_date_iso (ISO 8601 date if possible), "
    "and status (Pending by default). "
    "If the user does not specify a status, set it to 'Pending'. "
    "If the user says things like 'normal', treat it as 'Medium'. "
    "Return ONLY valid JSON — no explanations, no markdown, no text outside the JSON."
)

USER_TEMPLATE = (
    "Task text:\n"
    "\"\"\"{task_input}\"\"\"\n\n"
    "Now output a valid JSON object following the above schema, with sensible defaults for missing fields."
)
