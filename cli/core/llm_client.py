"""DeepSeek LLM client wrapper."""
import json
import os
import re
from pathlib import Path

import openai
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"


def _client() -> openai.OpenAI:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    return openai.OpenAI(api_key=api_key, base_url=BASE_URL)


def load_prompt(name: str, **placeholders) -> str:
    path = Path(__file__).resolve().parents[1] / "prompts" / f"{name}.txt"
    text = path.read_text(encoding="utf-8")
    if placeholders:
        # Escape braces not meant to be replaced to avoid KeyError
        for key, value in placeholders.items():
            text = text.replace("{" + key + "}", str(value))
    return text


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    return text.strip()


def call_deepseek(system_prompt: str, user_content: str = "", temperature: float = 0.3, max_tokens: int = 800) -> dict | None:
    """Call DeepSeek and attempt to parse JSON response. Returns None on error."""
    try:
        client = _client()
        messages = [{"role": "system", "content": system_prompt}]
        if user_content:
            messages.append({"role": "user", "content": user_content})
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        raw = response.choices[0].message.content or ""
        clean = _clean_json(raw)
        return json.loads(clean)
    except Exception as exc:
        # Log to stderr is the caller's responsibility; fail silently for resilience
        return {"_error": str(exc), "_raw": ""}
