import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def analyze_call(transcript: str) -> dict:
    """Takes a transcript, returns structured analysis as a dict."""

    prompt = f"""
You are an expert call center quality analyst. Analyze this customer service call transcript and return ONLY valid JSON with no extra text.

Transcript:
{transcript}

Return this exact JSON structure:
{{
  "overall_sentiment": "Positive | Neutral | Negative",
  "sentiment_score": <number from 0 to 10, where 0 is very negative and 10 is very positive>,
  "customer_sentiment": "Positive | Neutral | Negative",
  "agent_sentiment": "Positive | Neutral | Negative",
  "key_topics": ["topic1", "topic2", "topic3"],
  "call_summary": "<2-3 sentence summary of what happened>",
  "agent_strengths": ["strength1", "strength2"],
  "agent_improvements": ["improvement1", "improvement2"],
  "coaching_note": "<1 paragraph coaching tip for the agent>",
  "resolution_status": "Resolved | Unresolved | Escalated",
  "call_type": "Complaint | Inquiry | Support | Sales | Other"
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    return json.loads(raw)