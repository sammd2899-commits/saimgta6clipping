"""Google Gemini AI Client Backend (BYOK REST & Local Fallback).

Provides lightweight, zero-dependency access to Google AI Studio's Gemini models
(defaulting to gemini-2.5-flash) using standard Python urllib.
Gracefully returns None if GEMINI_API_KEY is not set or network is offline,
allowing callers to fall back to deterministic Python templates.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from config_manager import load_env

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def get_gemini_api_key() -> str | None:
    """Retrieves GEMINI_API_KEY from environment or local .env file."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        env_vars = load_env()
        key = env_vars.get("GEMINI_API_KEY")
    if key:
        key = key.strip()
        if key and not key.startswith("your_") and len(key) >= 10:
            return key
    return None


def has_gemini_api_key() -> bool:
    """Returns True if a valid GEMINI_API_KEY is configured."""
    return get_gemini_api_key() is not None


def call_gemini(
    prompt: str,
    system_instruction: str | None = None,
    model: str = DEFAULT_GEMINI_MODEL,
    temperature: float = 0.7,
    timeout: int = 20,
) -> str | None:
    """Calls Gemini REST API via Google AI Studio.

    Returns generated text on success, or None on missing key / error.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    body_dict: dict = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
        },
    }

    if system_instruction:
        body_dict["system_instruction"] = {
            "parts": [{"text": system_instruction}]
        }

    try:
        req_data = json.dumps(body_dict).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else str(e)
        print(f"[Gemini API Notice] HTTP {e.code}: {err_msg[:200]}")
    except Exception as e:
        print(f"[Gemini API Notice] Connection error: {e}")

    return None
