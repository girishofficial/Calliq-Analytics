"""SQLite persistence and manager-level queries for CallIQ."""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / "data" / "calliq.db"
DEMO_AGENTS = [
    ("Rahul Sharma", "rahul.sharma@example.com", "North America Support"),
    ("Priya Singh", "priya.singh@example.com", "North America Support"),
    ("Amit Verma", "amit.verma@example.com", "Enterprise Care"),
    ("Neha Patel", "neha.patel@example.com", "Enterprise Care"),
    ("Arjun Mehta", "arjun.mehta@example.com", "Customer Success"),
]


SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    team TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id INTEGER NOT NULL,
    call_timestamp TEXT NOT NULL,
    duration REAL NOT NULL DEFAULT 0,
    sentiment_score REAL NOT NULL DEFAULT 0,
    customer_mood TEXT NOT NULL,
    agent_mood TEXT NOT NULL,
    resolution TEXT NOT NULL,
    predicted_csat REAL NOT NULL DEFAULT 0,
    fcr INTEGER NOT NULL DEFAULT 0,
    talk_ratio_agent REAL NOT NULL DEFAULT 50,
    talk_ratio_customer REAL NOT NULL DEFAULT 50,
    summary TEXT NOT NULL,
    transcript TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    qa_score REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

CREATE TABLE IF NOT EXISTS coaching_insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    insight TEXT NOT NULL,
    evidence TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (call_id) REFERENCES calls(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_calls_agent ON calls(agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_timestamp ON calls(call_timestamp);
CREATE INDEX IF NOT EXISTS idx_coaching_category ON coaching_insights(category);
"""


def _now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_connection() as connection:
        connection.executescript(SCHEMA)
        connection.commit()


def ensure_demo_agents(connection=None):
    owns_connection = connection is None
    connection = connection or get_connection()
    try:
        for name, email, team in DEMO_AGENTS:
            connection.execute(
                """INSERT OR IGNORE INTO agents (name, email, team, created_at)
                   VALUES (?, ?, ?, ?)""",
                (name, email, team, _now()),
            )
        connection.commit()
    finally:
        if owns_connection:
            connection.close()


def get_agents():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, email, team, created_at FROM agents ORDER BY name"
        ).fetchall()
        return [dict(row) for row in rows]


def _number(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _csat_value(analysis):
    value = analysis.get("predicted_csat", 0)
    return _number(value.get("score") if isinstance(value, dict) else value)


def _fcr_value(analysis):
    value = analysis.get("fcr", False)
    if isinstance(value, dict):
        return bool(value.get("resolved_on_first_contact"))
    return bool(value)


def calculate_qa_score(analysis):
    sentiment = _number(analysis.get("sentiment_score"), 0) * 10
    csat = (_csat_value(analysis) / 5) * 100
    fcr = 100 if _fcr_value(analysis) else 55
    resolution = 100 if analysis.get("resolution_status") == "Resolved" else 65
    return round((sentiment * 0.35) + (csat * 0.3) + (fcr * 0.2) + (resolution * 0.15), 1)


def _evidence(transcript, insight):
    sentences = re.split(r"(?<=[.!?])\s+", transcript.strip())
    terms = set(re.findall(r"[a-z]{5,}", insight.lower()))
    for sentence in sentences:
        if len(terms.intersection(re.findall(r"[a-z]{5,}", sentence.lower()))) >= 1:
            return sentence[:280]
    return sentences[0][:280] if sentences and sentences[0] else "Evidence is available in the stored transcript."


def _coaching_category(insight):
    text = insight.lower()
    if any(term in text for term in ("empathy", "acknowledge", "frustrat", "listen")):
        return "Empathy / Acknowledgment"
    if any(term in text for term in ("confirm", "resolution", "resolve", "next step")):
        return "Resolution Confirmation"
    if any(term in text for term in ("clear", "explain", "communication", "concise")):
        return "Communication Clarity"
    return "Process Adherence"


def _severity(insight):
    text = insight.lower()
    if any(term in text for term in ("missed", "failed", "escalat", "urgent")):
        return "High"
    if any(term in text for term in ("could", "improve", "consider", "clarify")):
        return "Medium"
    return "Low"


def save_analysis(agent_id, transcript, analysis, call_timestamp=None, duration=None):
    timestamp = call_timestamp or _now()
    duration = _number(duration, 0)
    timeline = analysis.get("sentiment_timeline") or []
    if not duration and timeline:
        duration = _number(timeline[-1].get("minute"), 0)
    talk_ratio = analysis.get("talk_ratio") or {}
    improvements = analysis.get("agent_improvements") or []
    customer_mood = analysis.get("customer_sentiment", "Neutral")
    agent_mood = analysis.get("agent_sentiment", "Neutral")
    csat = _csat_value(analysis)
    fcr = 1 if _fcr_value(analysis) else 0
    created_at = _now()
    qa_score = calculate_qa_score(analysis)

    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO calls (
                agent_id, call_timestamp, duration, sentiment_score, customer_mood,
                agent_mood, resolution, predicted_csat, fcr, talk_ratio_agent,
                talk_ratio_customer, summary, transcript, analysis_json, qa_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent_id,
                timestamp,
                duration,
                _number(analysis.get("sentiment_score")),
                customer_mood,
                agent_mood,
                analysis.get("resolution_status", "Unresolved"),
                csat,
                fcr,
                _number(talk_ratio.get("agent"), 50),
                _number(talk_ratio.get("customer"), 50),
                analysis.get("call_summary", ""),
                transcript,
                json.dumps(analysis),
                qa_score,
                created_at,
            ),
        )
        call_id = cursor.lastrowid
        for insight in improvements:
            connection.execute(
                """INSERT INTO coaching_insights
                   (call_id, category, severity, insight, evidence, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    call_id,
                    _coaching_category(insight),
                    _severity(insight),
                    insight,
                    _evidence(transcript, insight),
                    created_at,
                ),
            )
        connection.commit()
    return call_id


def _call_filters(params):
    clauses = []
    values = []
    if params.get("agent_id"):
        clauses.append("c.agent_id = ?")
        values.append(int(params["agent_id"]))
    if params.get("sentiment"):
        clauses.append("c.customer_mood = ?")
        values.append(params["sentiment"])
    if params.get("fcr") in ("true", "false"):
        clauses.append("c.fcr = ?")
        values.append(1 if params["fcr"] == "true" else 0)
    if params.get("min_qa"):
        clauses.append("c.qa_score >= ?")
        values.append(float(params["min_qa"]))
    if params.get("from"):
        clauses.append("date(c.call_timestamp) >= date(?)")
        values.append(params["from"])
    if params.get("to"):
        clauses.append("date(c.call_timestamp) <= date(?)")
        values.append(params["to"])
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", values


def _call_select():
    return """SELECT c.*, a.name AS agent_name, a.team AS agent_team
              FROM calls c JOIN agents a ON a.id = c.agent_id"""


def _call_row(row):
    item = dict(row)
    item["fcr"] = bool(item["fcr"])
    item["analysis"] = json.loads(item.pop("analysis_json"))
    return item


def get_calls(params=None):
    params = params or {}
    where, values = _call_filters(params)
    limit = min(max(int(params.get("limit", 100)), 1), 500)
    with get_connection() as connection:
        rows = connection.execute(
            _call_select() + where + " ORDER BY c.call_timestamp DESC LIMIT ?",
            values + [limit],
        ).fetchall()
        return [_call_row(row) for row in rows]


def get_call(call_id):
    with get_connection() as connection:
        row = connection.execute(_call_select() + " WHERE c.id = ?", (call_id,)).fetchone()
        if not row:
            return None
        item = _call_row(row)
        insights = connection.execute(
            "SELECT id, category, severity, insight, evidence, created_at FROM coaching_insights WHERE call_id = ? ORDER BY id",
            (call_id,),
        ).fetchall()
        item["coaching_insights"] = [dict(insight) for insight in insights]
        return item


def get_overview():
    with get_connection() as connection:
        row = connection.execute(
            """SELECT COUNT(*) AS calls_analyzed,
                      COALESCE(AVG(qa_score), 0) AS average_qa_score,
                      COALESCE(AVG(predicted_csat), 0) AS average_csat,
                      COALESCE(AVG(fcr) * 100, 0) AS fcr_rate
               FROM calls"""
        ).fetchone()
        coaching = connection.execute("SELECT COUNT(DISTINCT call_id) AS count FROM coaching_insights").fetchone()["count"]
        return {
            "calls_analyzed": row["calls_analyzed"],
            "average_qa_score": round(row["average_qa_score"], 1),
            "average_csat": round(row["average_csat"], 1),
            "fcr_rate": round(row["fcr_rate"], 1),
            "calls_requiring_coaching": coaching,
        }


def get_agent_performance():
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT a.id, a.name, a.email, a.team,
                      COUNT(DISTINCT c.id) AS calls,
                      COALESCE(AVG(c.qa_score), 0) AS qa_score,
                      COALESCE(AVG(c.predicted_csat), 0) AS csat,
                      COALESCE(AVG(c.fcr) * 100, 0) AS fcr,
                      COUNT(DISTINCT ci.call_id) AS coaching_flags
               FROM agents a
               LEFT JOIN calls c ON c.agent_id = a.id
               LEFT JOIN coaching_insights ci ON ci.call_id = c.id
               GROUP BY a.id
               ORDER BY qa_score DESC, a.name"""
        ).fetchall()
        return [
            {**dict(row), "qa_score": round(row["qa_score"], 1), "csat": round(row["csat"], 1), "fcr": round(row["fcr"], 1)}
            for row in rows
        ]


def get_agent_detail(agent_id):
    with get_connection() as connection:
        agent = connection.execute("SELECT id, name, email, team FROM agents WHERE id = ?", (agent_id,)).fetchone()
        if not agent:
            return None
        summary = connection.execute(
            """SELECT COUNT(*) AS calls, COALESCE(AVG(qa_score), 0) AS qa_score,
                      COALESCE(AVG(predicted_csat), 0) AS csat, COALESCE(AVG(fcr) * 100, 0) AS fcr
               FROM calls WHERE agent_id = ?""", (agent_id,)
        ).fetchone()
        sentiment = connection.execute(
            "SELECT customer_mood AS sentiment, COUNT(*) AS count FROM calls WHERE agent_id = ? GROUP BY customer_mood",
            (agent_id,),
        ).fetchall()
        trend = connection.execute(
            """SELECT date(call_timestamp) AS date, ROUND(AVG(qa_score), 1) AS qa_score
               FROM calls WHERE agent_id = ? GROUP BY date(call_timestamp) ORDER BY date""", (agent_id,)
        ).fetchall()
        opportunities = connection.execute(
            """SELECT ci.category, ci.severity, ci.insight, ci.evidence, c.id AS call_id,
                      c.call_timestamp FROM coaching_insights ci JOIN calls c ON c.id = ci.call_id
               WHERE c.agent_id = ? ORDER BY c.call_timestamp DESC""", (agent_id,)
        ).fetchall()
        return {
            "agent": dict(agent),
            "metrics": {"calls": summary["calls"], "qa_score": round(summary["qa_score"], 1), "csat": round(summary["csat"], 1), "fcr": round(summary["fcr"], 1)},
            "sentiment_distribution": [dict(row) for row in sentiment],
            "qa_trend": [dict(row) for row in trend],
            "recent_calls": get_calls({"agent_id": agent_id, "limit": 10}),
            "coaching_opportunities": [dict(row) for row in opportunities],
        }


def get_coaching_opportunities():
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT category, COUNT(*) AS calls, MIN(severity) AS severity
               FROM coaching_insights GROUP BY category ORDER BY calls DESC, category"""
        ).fetchall()
        return [dict(row) for row in rows]


def get_coaching_calls(category):
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT c.id, c.call_timestamp, a.name AS agent_name, ci.severity,
                      ci.insight, ci.evidence FROM coaching_insights ci
               JOIN calls c ON c.id = ci.call_id JOIN agents a ON a.id = c.agent_id
               WHERE ci.category = ? ORDER BY c.call_timestamp DESC""", (category,)
        ).fetchall()
        return [dict(row) for row in rows]


init_db()
