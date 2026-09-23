"""Create local demo data for the CallIQ manager dashboard."""

import argparse
import random
import sqlite3
from datetime import datetime, timedelta

from database import DEMO_AGENTS, DATABASE_PATH, get_connection, init_db, save_analysis


CUSTOMER_LINES = [
    "I have already called twice and nobody has fixed this.",
    "The charge on my account does not look right.",
    "I need help changing the delivery address before it ships.",
    "The new plan sounds useful, but I want to understand the terms.",
    "The issue started after the last update and is still happening.",
]

IMPROVEMENTS = [
    "Agent could acknowledge the customer's frustration earlier.",
    "Agent should confirm the resolution and next steps before closing.",
    "Agent could explain the process more clearly and check for understanding.",
    "Agent should follow the escalation process and document the next action.",
]

SUMMARIES = [
    "The customer called about an account issue. The agent reviewed the details, explained the available options, and agreed on a next step.",
    "The customer needed help with a service request. The agent identified the issue and worked toward a resolution during the call.",
    "The customer questioned a recent change. The agent clarified the policy and confirmed what would happen after the call.",
]


def build_analysis(rng, index):
    sentiment = rng.choices(["Positive", "Neutral", "Negative"], weights=[4, 4, 2])[0]
    score_range = {"Positive": (7, 10), "Neutral": (4, 7), "Negative": (1, 5)}[sentiment]
    sentiment_score = rng.randint(*score_range)
    csat = max(1, min(5, round(sentiment_score / 2 + rng.choice([-1, 0, 0, 1]))))
    resolved = sentiment != "Negative" and rng.random() > 0.18
    resolution = "Resolved" if resolved else rng.choice(["Unresolved", "Escalated"])
    customer_line = CUSTOMER_LINES[index % len(CUSTOMER_LINES)]
    improvement_count = 1 if rng.random() < 0.62 else 2
    improvements = rng.sample(IMPROVEMENTS, improvement_count)
    strengths = rng.sample(
        [
            "Maintained a calm and professional tone.",
            "Asked focused questions to understand the issue.",
            "Explained the available options clearly.",
            "Confirmed the customer's preferred next step.",
        ],
        2,
    )
    return {
        "overall_sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "customer_sentiment": sentiment,
        "agent_sentiment": rng.choice(["Positive", "Positive", "Neutral"]),
        "key_topics": rng.sample(["billing", "delivery", "account access", "plan change", "technical support"], 3),
        "call_summary": SUMMARIES[index % len(SUMMARIES)],
        "agent_strengths": strengths,
        "agent_improvements": improvements,
        "coaching_note": "Keep the conversation structured and close by repeating the agreed action and timing.",
        "resolution_status": resolution,
        "call_type": rng.choice(["Support", "Inquiry", "Complaint", "Sales"]),
        "talk_ratio": {"agent": rng.randint(42, 64), "customer": 0},
        "sentiment_timeline": [{"minute": minute, "score": max(0, min(10, sentiment_score + rng.randint(-2, 2)))} for minute in range(1, 6)],
        "predicted_csat": {
            "score": csat,
            "label": ["Very Dissatisfied", "Dissatisfied", "Neutral", "Satisfied", "Very Satisfied"][csat - 1],
            "confidence": rng.choice(["Medium", "High"]),
            "reasoning": "The predicted score reflects the customer's tone, outcome, and clarity of the next step.",
        },
        "fcr": {
            "resolved_on_first_contact": resolved,
            "confidence": rng.choice(["Medium", "High"]),
            "risk_of_callback": "Low" if resolved else rng.choice(["Medium", "High"]),
            "reasoning": "The issue was addressed during the interaction, although follow-up risk remains when the outcome is not confirmed.",
        },
        "_customer_line": customer_line,
    }


def seed(reset=False):
    init_db()
    with get_connection() as connection:
        if reset:
            connection.execute("DELETE FROM coaching_insights")
            connection.execute("DELETE FROM calls")
            connection.commit()
        existing = connection.execute("SELECT COUNT(*) AS count FROM calls").fetchone()["count"]
        agents = connection.execute("SELECT id, name FROM agents ORDER BY id").fetchall()
    if existing and not reset:
        print("Demo data already exists. Use --reset to recreate it.")
        return

    rng = random.Random(20260923)
    now = datetime.utcnow()
    for index in range(40):
        analysis = build_analysis(rng, index)
        transcript = "Customer: {} Agent: {}".format(
            analysis.pop("_customer_line"),
            "I understand. Let me review that with you and confirm the next step before we finish.",
        )
        analysis["talk_ratio"]["customer"] = 100 - analysis["talk_ratio"]["agent"]
        timestamp = (now - timedelta(days=rng.randint(0, 44), hours=rng.randint(0, 12))).replace(microsecond=0).isoformat() + "Z"
        agent_id = agents[index % len(agents)]["id"]
        save_analysis(agent_id, transcript, analysis, call_timestamp=timestamp, duration=rng.randint(4, 18))
    print("Seeded 40 demo calls for {} agents into {}".format(len(agents), DATABASE_PATH))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the CallIQ SQLite database with local demo data.")
    parser.add_argument("--reset", action="store_true", help="Delete existing calls before seeding.")
    seed(parser.parse_args().reset)
