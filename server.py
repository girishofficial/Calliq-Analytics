from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
from groq import Groq
from dotenv import load_dotenv
import json

from database import (
    ensure_demo_agents,
    get_agent_detail,
    get_agents,
    get_agent_performance,
    get_call,
    get_calls,
    get_coaching_calls,
    get_coaching_opportunities,
    get_overview,
    init_db,
    save_analysis,
)

load_dotenv()

app = Flask(__name__)
CORS(app)
init_db()
ensure_demo_agents()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def transcribe_audio(file_path: str) -> str:
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            response_format="text"
        )
    return transcription


def analyze_call(transcript: str) -> dict:
    prompt = f"""
You are an expert call center quality analyst. Analyze this customer service call transcript and return ONLY valid JSON with no extra text.

Transcript:
{transcript}

Return this exact JSON structure:
{{
  "overall_sentiment": "Positive | Neutral | Negative",
  "sentiment_score": <number from 0 to 10>,
  "customer_sentiment": "Positive | Neutral | Negative",
  "agent_sentiment": "Positive | Neutral | Negative",
  "key_topics": ["topic1", "topic2", "topic3"],
  "call_summary": "<2-3 sentence summary>",
  "agent_strengths": ["strength1", "strength2"],
  "agent_improvements": ["improvement1", "improvement2"],
  "coaching_note": "<1 paragraph coaching tip>",
  "resolution_status": "Resolved | Unresolved | Escalated",
  "call_type": "Complaint | Inquiry | Support | Sales | Other",
  "talk_ratio": {{
    "agent": <percentage number 0-100>,
    "customer": <percentage number 0-100>
  }},
  "sentiment_timeline": [
    {{"minute": 1, "score": <0-10>}},
    {{"minute": 2, "score": <0-10>}},
    {{"minute": 3, "score": <0-10>}},
    {{"minute": 4, "score": <0-10>}},
    {{"minute": 5, "score": <0-10>}}
  ],
  "predicted_csat": {{
    "score": <number from 1 to 5>,
    "label": "Very Dissatisfied | Dissatisfied | Neutral | Satisfied | Very Satisfied",
    "confidence": "Low | Medium | High",
    "reasoning": "<1-2 sentences explaining why this CSAT score was predicted>"
  }},
  "fcr": {{
    "resolved_on_first_contact": <true or false>,
    "confidence": "Low | Medium | High",
    "risk_of_callback": "Low | Medium | High",
    "reasoning": "<1-2 sentences on whether the issue was fully resolved or if the customer is likely to call back>"
  }}
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    suffix = os.path.splitext(file.filename)[1]
    agent_id = request.form.get("agent_id")
    if not agent_id:
        agents = get_agents()
        agent_id = agents[0]["id"] if agents else None
    try:
        agent_id = int(agent_id)
    except (TypeError, ValueError):
        return jsonify({"error": "A valid agent_id is required"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        transcript = transcribe_audio(tmp_path)
        analysis = analyze_call(transcript)
        save_analysis(agent_id, transcript, analysis)
        return jsonify({"transcript": transcript, "analysis": analysis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.route("/api/agents", methods=["GET"])
def agents():
    return jsonify(get_agents())


@app.route("/api/manager/overview", methods=["GET"])
def manager_overview():
    return jsonify(get_overview())


@app.route("/api/manager/agents", methods=["GET"])
def manager_agents():
    return jsonify(get_agent_performance())


@app.route("/api/manager/agents/<int:agent_id>", methods=["GET"])
def manager_agent(agent_id):
    result = get_agent_detail(agent_id)
    if result is None:
        return jsonify({"error": "Agent not found"}), 404
    return jsonify(result)


@app.route("/api/manager/calls", methods=["GET"])
def manager_calls():
    return jsonify(get_calls(request.args.to_dict()))


@app.route("/api/manager/calls/<int:call_id>", methods=["GET"])
def manager_call(call_id):
    result = get_call(call_id)
    if result is None:
        return jsonify({"error": "Call not found"}), 404
    return jsonify(result)


@app.route("/api/manager/coaching", methods=["GET"])
def manager_coaching():
    return jsonify(get_coaching_opportunities())


@app.route("/api/manager/coaching/<path:category>", methods=["GET"])
def manager_coaching_calls(category):
    return jsonify(get_coaching_calls(category))


if __name__ == "__main__":
    app.run(debug=True, port=5000)