# backend/services/llm_service.py
import requests
import json
from typing import Optional

OLLAMA_API = "http://localhost:11434/api/generate"
MODEL_NAME = "aidgen"  # name of model built with Modelfile

def call_ollama(prompt: str, model: str = MODEL_NAME, max_tokens:int=256, top_p:float=0.95):
    """
    Call local Ollama HTTP API. Returns response text (raw).
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": 0.1,
        "max_length": max_tokens,
        "top_p": top_p
    }
    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=8)
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Ollama API error: {e}")

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama returned {resp.status_code}: {resp.text}")

    # Ollama returns JSON with 'results' or a raw text field; handle both.
    try:
        data = resp.json()
    except Exception:
        return resp.text

    # Some Ollama versions echo an array of tokens or 'generated_text'
    if isinstance(data, dict):
        if "response" in data:
            return data["response"]
        if "results" in data and isinstance(data["results"], list) and data["results"]:
            # try join text fields
            texts = []
            for r in data["results"]:
                t = r.get("text") or r.get("generated_text") or r.get("response")
                if t:
                    texts.append(t)
            return "\n".join(texts).strip()
    return json.dumps(data)
