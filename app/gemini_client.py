import json
from typing import Any, Optional
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, DEFAULT_MODEL


_client: Optional[genai.Client] = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _build_prompt(prompt: str, data: Optional[dict]) -> str:
    if not data:
        return prompt
    context_lines = json.dumps(data, indent=2)
    return f"{prompt}\n\n--- Context Data ---\n{context_lines}"


def _dict_to_schema(schema_dict: dict) -> types.Schema:
    """Recursively convert a plain JSON Schema dict to a google.genai types.Schema."""
    type_map = {
        "string": types.Type.STRING,
        "integer": types.Type.INTEGER,
        "number": types.Type.NUMBER,
        "boolean": types.Type.BOOLEAN,
        "array": types.Type.ARRAY,
        "object": types.Type.OBJECT,
    }

    kwargs: dict[str, Any] = {}
    raw_type = schema_dict.get("type", "string")
    kwargs["type"] = type_map.get(raw_type, types.Type.STRING)

    if "description" in schema_dict:
        kwargs["description"] = schema_dict["description"]

    if "enum" in schema_dict:
        kwargs["enum"] = schema_dict["enum"]

    if "properties" in schema_dict:
        kwargs["properties"] = {
            k: _dict_to_schema(v) for k, v in schema_dict["properties"].items()
        }

    if "required" in schema_dict:
        kwargs["required"] = schema_dict["required"]

    if "items" in schema_dict:
        kwargs["items"] = _dict_to_schema(schema_dict["items"])

    if "minimum" in schema_dict:
        kwargs["minimum"] = schema_dict["minimum"]

    if "maximum" in schema_dict:
        kwargs["maximum"] = schema_dict["maximum"]

    return types.Schema(**kwargs)


async def generate_structured(
    prompt: str,
    response_schema: dict,
    data: Optional[dict] = None,
    model: Optional[str] = None,
    system_instruction: Optional[str] = None,
    temperature: float = 1.0,
    file_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
    use_google_search: bool = False,
) -> dict:
    client = get_client()
    model_name = model or DEFAULT_MODEL
    full_prompt = _build_prompt(prompt, data)

    contents: list[Any] = [full_prompt]
    if file_bytes and mime_type:
        contents.append(
            types.Part.from_bytes(
                data=file_bytes,
                mime_type=mime_type
            )
        )

    config_kwargs: dict[str, Any] = {
        "response_mime_type": "application/json",
        "response_schema": _dict_to_schema(response_schema),
        "temperature": temperature,
    }
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
        
    if use_google_search:
        config_kwargs["tools"] = [{"google_search": {}}]

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(**config_kwargs),
    )

    return json.loads(response.text)
