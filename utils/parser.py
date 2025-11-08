import json
import re
from jsonschema import validate, ValidationError


class JSONParseError(Exception):
    """Raised when model output cannot be parsed or validated as JSON."""
    pass


# Regex pattern to extract the first {...} JSON block from text
CURLY_JSON_RE = re.compile(r"\{[\s\S]*\}")


def extract_and_validate_json(text: str, schema: dict) -> dict:
    """
    Extract the first JSON object from a string,
    parse it, and validate it against a provided JSON schema.

    Args:
        text (str): The raw text returned by the model.
        schema (dict): The JSON schema to validate against.

    Returns:
        dict: Validated JSON object.

    Raises:
        JSONParseError: If no valid JSON object is found or validation fails.
    """
    # Extract the first {...} JSON-like block
    match = CURLY_JSON_RE.search(text)
    if not match:
        raise JSONParseError("No JSON object found in model output.")

    json_text = match.group(0)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise JSONParseError(f"Invalid JSON format: {e}")

    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise JSONParseError(f"JSON does not match schema: {e.message}")

    return data