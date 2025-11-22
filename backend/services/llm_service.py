# backend/services/llm_service.py

import requests
import json
from typing import Dict, Any

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL_NAME = "aidgen:latest"

def call_ollama(prompt: str, model: str = MODEL_NAME) -> str:
    """Calls the Ollama local model and returns the raw text response."""

    try:
        response = requests.post(
            OLLAMA_API,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"[Ollama Error] {e}")
        raise


def extract_json(raw: str) -> dict:
    """Extracts JSON from raw LLM output safely."""

    raw = raw.strip()

    # If fenced code blocks exist
    if "```json" in raw:
        try:
            raw = raw.split("```json")[1].split("```")[0].strip()
        except:
            pass

    elif "```" in raw:
        try:
            raw = raw.split("```")[1].split("```")[0].strip()
        except:
            pass

    # Find first { and last }
    if "{" in raw and "}" in raw:
        try:
            raw = raw[raw.index("{"): raw.rindex("}") + 1]
        except:
            pass

    # Try to parse JSON
    try:
        return json.loads(raw)
    except Exception as e:
        print(f"[JSON Parse Error] Raw Output: {raw}")
        print(f"Error: {e}")
        return None


def generate_emergency_response(emergency_type: str, location: str = "") -> Dict[str, Any]:
    """Generates a structured emergency response using LLM."""

    prompt = f"""
You are an emergency response assistant. Provide a structured response for a {emergency_type} emergency.

Location: {location or 'Not specified'}

Output ONLY a JSON object with this structure:
{{
  "title": "string",
  "summary": "string",
  "steps": ["step1", "step2", "step3"],
  "warnings": ["warning1", "warning2"],
  "sms_template": "short sms message"
}}
(All fields required. No markdown. No explanations.)
"""

    try:
        raw = call_ollama(prompt)
        data = extract_json(raw)

        # Validate
        required = ["title", "summary", "steps", "warnings", "sms_template"]

        if not data or not all(k in data for k in required):
            raise ValueError("Invalid JSON from model")

        return data

    except Exception as e:
        print(f"[Emergency Response Error] {e}")

        # Fallback response
        return {
            "title": f"{emergency_type.capitalize()} Emergency",
            "summary": "Emergency information is currently unavailable.",
            "steps": [
                "Stay calm and assess your surroundings.",
                "Move to a safer location if possible.",
                "Contact emergency services immediately.",
            ],
            "warnings": ["Follow official safety instructions.", "Avoid unnecessary risks."],
            "sms_template": f"EMERGENCY: {emergency_type.upper()} - Seek safety and follow emergency guidelines."
        }
