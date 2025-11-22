# backend/app.py
import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory

# ----------------------------------------------------------------------
# Ensure backend folder is discoverable
# ----------------------------------------------------------------------
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ----------------------------------------------------------------------
# IMPORT SERVICES
# ----------------------------------------------------------------------
from backend.services import (
    resource_service,
    template_service,
    translate_service,
    SOSService
)
from backend.services.llm_service import call_ollama, extract_json, generate_emergency_response

# ----------------------------------------------------------------------
# INITIALIZE FLASK APP
# ----------------------------------------------------------------------
app = Flask(__name__, static_folder="../frontend", static_url_path="")

# SOS service init
sos_service = SOSService()

# ----------------------------------------------------------------------
# FRONTEND ROUTES
# ----------------------------------------------------------------------
@app.route("/")
def serve_index():
    return send_from_directory("../frontend", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory("../frontend", path)

# ----------------------------------------------------------------------
# RESOURCES API
# ----------------------------------------------------------------------
@app.route("/api/resources", methods=["GET"])
def api_resources():
    q = request.args.get("q", "")
    res = resource_service.find_resources_by_keyword(q) if q else resource_service.get_all_resources()
    return jsonify({"ok": True, "resources": res})

# ----------------------------------------------------------------------
# FALLBACK TEMPLATE API
# ----------------------------------------------------------------------
@app.route("/api/fallback/<kind>", methods=["GET"])
def api_fallback(kind):
    tpl = template_service.load_template(kind)
    if not tpl:
        return jsonify({"ok": False, "error": "Template not found"}), 404
    return jsonify({"ok": True, "template": tpl})

# ----------------------------------------------------------------------
# TRANSLATION API
# ----------------------------------------------------------------------
@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json() or {}
    text = data.get("text", "")
    source = data.get("from", "en")
    target = data.get("to", "kn")

    if not text:
        return jsonify({"ok": False, "error": "No text provided"}), 400

    translated = translate_service.translate_text(text, source, target)
    if not translated:
        return jsonify({"ok": False, "error": "Translation unavailable"}), 500

    return jsonify({"ok": True, "translated": translated})

# ----------------------------------------------------------------------
# ALERT API
# ----------------------------------------------------------------------
@app.route("/api/alert", methods=["POST"])
def api_alert():
    data = request.get_json() or {}
    emergency_type = data.get("type", "general")
    location = data.get("location", "[LOCATION UNKNOWN]")

    template = template_service.get_fallback_template(emergency_type)
    if not template:
        return jsonify({"ok": False, "error": "Template not found"}), 404

    sms = template.get("sms_template", "").replace("[LOCATION]", location)
    template["sms_template"] = sms

    return jsonify({
        "ok": True,
        "type": emergency_type,
        "location": location,
        "data": template
    })

# ----------------------------------------------------------------------
# SOS EMERGENCY SMS
# ----------------------------------------------------------------------
@app.route("/api/sos", methods=["POST"])
def api_sos():
    payload = request.get_json() or {}
    emergency_type = payload.get("type", "general")
    latitude = payload.get("latitude")
    longitude = payload.get("longitude")
    location_desc = payload.get("location")

    try:
        result = sos_service.send_emergency_sms(
            emergency_type=emergency_type,
            latitude=latitude,
            longitude=longitude,
            location_desc=location_desc
        )
        status_code = 200 if result.get("success") else 500
        return jsonify({"ok": result.get("success"), "details": result}), status_code

    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500

# ----------------------------------------------------------------------
# EMERGENCY GENERATION API (LLM)
# ----------------------------------------------------------------------
@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json() or {}
    query = data.get("query", "")
    kind = data.get("kind", "")
    location = data.get("location", "")
    language = data.get("language", "en")

    if not query and not kind:
        return jsonify({"ok": False, "error": "Query or type required"}), 400

    prompt = (
        "You are AidGen, an offline emergency assistant.\n"
        "Return ONLY valid JSON with: title, summary, steps[], warnings[], sms_template.\n"
        "If unsure return {\"error\": \"unknown\"}.\n\n"
        f"CONTEXT:\nKind: {kind}\nLocation: {location}\nQuery: {query}\n"
    )

    try:
        raw = call_ollama(prompt)
        parsed = json.loads(raw)
        return jsonify({"ok": True, "result": parsed})

    except Exception as e:
        tpl = template_service.load_template(kind)
        if tpl:
            return jsonify({"ok": True, "fallback": True, "result": tpl})
        return jsonify({"ok": False, "error": "LLM failed", "details": str(e)}), 500

# ----------------------------------------------------------------------
# EMERGENCY INSTRUCTIONS API
# ----------------------------------------------------------------------
@app.route("/api/emergency/instructions", methods=["POST"])
def api_emergency_instructions():
    data = request.get_json() or {}
    emergency_type = data.get("type", "general")
    location = data.get("location", "")

    try:
        response = generate_emergency_response(emergency_type, location)
        return jsonify({"ok": True, "instructions": response})

    except Exception as e:
        tpl = template_service.load_template(emergency_type)
        if tpl:
            return jsonify({"ok": True, "fallback": True, "instructions": tpl})
        return jsonify({"ok": False, "error": "Could not load instructions"}), 500

# ----------------------------------------------------------------------
# AI CHATBOT API (Local + Ollama Fallback)
# ----------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "")
    help_context = data.get("help_context", False)
    emergency_type = data.get("emergency_type", "general")

    if not message:
        return jsonify({"ok": False, "error": "No message provided"}), 400

    # Prebuilt local responses
    local_responses = {
        "hello": "Hi there! How can I assist you today?",
        "help": "Sure! Ask me anything and I will guide you.",
        "bye": "Goodbye! Stay safe!",
    }

    reply = local_responses.get(message.lower())
    if not reply:
        # Fallback to Ollama
        prompt = (
            f"You are AidGen Chatbot, an emergency response assistant.\n"
            f"Current emergency context: {emergency_type.upper()}\n\n"
            f"Answer concisely and helpfully using structured guidance.\n"
            f"Return ONLY valid JSON with: title, summary, steps (array), warnings (array), sms_template.\n"
            f"User: {message}\nAidGen:\n"
        )
        try:
            response = call_ollama(prompt)
            structured = extract_json(response)
            if structured and "summary" in structured:
                reply = structured.get("summary", "")
            else:
                reply = "I'm not sure about that. Can you rephrase?"
        except Exception as e:
            reply = "⚠️ Error: Ollama backend failed."

    return jsonify({"ok": True, "reply": reply})

# ----------------------------------------------------------------------
# RUN SERVER
# ----------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
