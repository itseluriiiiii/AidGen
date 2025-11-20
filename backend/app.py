# backend/app.py
import json
import os
from flask import Flask, request, jsonify
from services import fallback_templates, resource_service, translate_service, llm_service

app = Flask(__name__)

@app.route("/api/resources", methods=["GET"])
def api_resources():
    q = request.args.get("q", "")
    if q:
        res = resource_service.find_resources_by_keyword(q)
    else:
        res = resource_service.get_all_resources()
    return jsonify({"ok": True, "resources": res})

@app.route("/api/fallback/<kind>", methods=["GET"])
def api_fallback(kind):
    tpl = fallback_templates.load_template(kind)
    if tpl is None:
        return jsonify({"ok": False, "error": "no template"}), 404
    return jsonify({"ok": True, "template": tpl})

@app.route("/api/translate", methods=["POST"])
def api_translate():
    body = request.get_json() or {}
    text = body.get("text", "")
    to_lang = body.get("to", "kn")
    if not text:
        return jsonify({"ok": False, "error": "no text"}), 400
    translated = translate_service.translate_text(text, "en", to_lang)
    if translated is None:
        return jsonify({"ok": False, "error": "translation unavailable"}), 500
    return jsonify({"ok": True, "translated": translated})

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """
    Accepts { query: "...", location: "...", language: "en" }
    Calls local Ollama model to generate structured JSON. If Ollama unreachable or returns invalid JSON,
    return the fallback template.
    """
    body = request.get_json() or {}
    query = body.get("query", "")
    kind = body.get("kind", "").lower()  # optional: 'earthquake', 'flood', 'fire'
    location = body.get("location", "")
    language = body.get("language", "en")

    # minimal validation
    if not query and not kind:
        return jsonify({"ok": False, "error": "query or kind required"}), 400

    # Build structured prompt for Ollama
    instruction = {
        "schema": {
            "title":"string",
            "summary":"string",
            "steps":["string"],
            "sms_template":"string",
            "warnings":["string"]
        },
        "context": {
            "query": query,
            "location": location,
            "kind": kind,
            "language": language
        }
    }

    prompt_text = (
        "You are AidGen, an offline emergency assistant. "
        "Produce JSON exactly matching the schema: {title, summary, steps (array), sms_template, warnings (array)}. "
        "Limit steps to 3-8 short actionable items. Keep SMS <= 160 chars. Do NOT hallucinate locations or phones. "
        "If you cannot generate, output JSON with 'error' field."
        f"\n\nCONTEXT:\n{json.dumps(instruction['context'])}\n\nTEMPLATE if needed: {''}"
    )

    # Try call Ollama
    try:
        raw = llm_service.call_ollama(prompt_text)
        # Try parse JSON inside response (strip surrounding text)
        parsed = None
        import re, json
        # try to find JSON object in raw
        m = re.search(r"(\{(?:.|\n)*\})", raw)
        if m:
            js_text = m.group(1)
            parsed = json.loads(js_text)
        else:
            # fallback: try raw as json
            parsed = json.loads(raw)
        # If parsed contains error or missing fields, fallback
        if not isinstance(parsed, dict) or "steps" not in parsed:
            raise ValueError("invalid structure from LLM")
        return jsonify({"ok": True, "result": parsed})
    except Exception as e:
        # fallback: use template if kind available, else return error wrapper
        if kind:
            tpl = fallback_templates.load_template(kind)
            if tpl:
                # optionally tailor small placeholders
                # fill placeholder {location} in sms_template
                sms = tpl.get("sms_template", "")
                if "{location}" in sms and location:
                    sms = sms.replace("{location}", location)
                tpl["sms_template"] = sms
                return jsonify({"ok": True, "result": tpl, "fallback": True})
        return jsonify({"ok": False, "error": "LLM unavailable or returned invalid output", "detail": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
