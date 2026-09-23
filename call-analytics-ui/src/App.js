import React, { useState, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// ── Theme tokens ────────────────────────────────────────────────
const DARK = {
  bg: "#0A0F1E",
  surface: "#141929",
  surfaceHi: "#1C2438",
  border: "#1E2D4A",
  accent: "#2563EB",
  accentLo: "#1E3A8A",
  accentGlow: "rgba(37,99,235,0.15)",
  green: "#10B981",
  yellow: "#F59E0B",
  red: "#EF4444",
  textPri: "#F1F5F9",
  textSec: "#64748B",
  textMid: "#94A3B8",
  toggleBg: "#1C2438",
  toggleIcon: "☀️",
  toggleLabel: "Light mode",
};

// RingCentral brand: blue #0684bc, orange #ff7a00
const LIGHT = {
  bg: "#F0F4F8",
  surface: "#FFFFFF",
  surfaceHi: "#EBF4FA",
  border: "#C9DFF0",
  accent: "#0684bc",
  accentLo: "#D0EAF5",
  accentGlow: "rgba(6,132,188,0.10)",
  green: "#0a7c5c",
  yellow: "#b45309",
  red: "#DC2626",
  textPri: "#0C1929",
  textSec: "#4A6375",
  textMid: "#2D5068",
  toggleBg: "#EBF4FA",
  toggleIcon: "🌙",
  toggleLabel: "Dark mode",
};

const mono = "'JetBrains Mono', monospace";
const sans = "'Inter', sans-serif";

// ── Style factories (theme-aware) ────────────────────────────────
const makeStyles = (C) => ({
  app: {
    fontFamily: sans,
    background: C.bg,
    minHeight: "100vh",
    color: C.textPri,
    display: "flex",
    flexDirection: "column",
    transition: "background 0.25s, color 0.25s",
  },
  topbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 32px",
    height: 56,
    borderBottom: `1px solid ${C.border}`,
    background: C.surface,
    position: "sticky",
    top: 0,
    zIndex: 10,
    transition: "background 0.25s, border-color 0.25s",
  },
  logo: {
    fontFamily: mono,
    fontSize: 15,
    fontWeight: 500,
    color: C.textPri,
    letterSpacing: "-0.02em",
  },
  logoAccent: { color: C.accent },
  badge: {
    fontSize: 10,
    fontFamily: mono,
    background: C.accentLo,
    color: C.accent,
    padding: "2px 8px",
    borderRadius: 4,
    border: `1px solid ${C.accent}`,
  },
  themeToggle: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "6px 14px",
    borderRadius: 20,
    border: `1px solid ${C.border}`,
    background: C.toggleBg,
    cursor: "pointer",
    fontSize: 12,
    color: C.textMid,
    fontFamily: mono,
    transition: "all 0.2s",
    userSelect: "none",
  },
  topbarRight: {
    display: "flex",
    alignItems: "center",
    gap: 12,
  },
  body: {
    display: "flex",
    flex: 1,
  },
  sidebar: {
    width: 280,
    borderRight: `1px solid ${C.border}`,
    padding: 24,
    display: "flex",
    flexDirection: "column",
    gap: 24,
    background: C.surface,
    transition: "background 0.25s, border-color 0.25s",
  },
  main: {
    flex: 1,
    padding: 32,
    overflowY: "auto",
  },
  welcome: {
    flex: 1,
    minHeight: "calc(100vh - 56px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px 24px",
    perspective: 1200,
    position: "relative",
    overflow: "hidden",
  },
  welcomeBackdrop: {
    position: "absolute",
    inset: 0,
    overflow: "hidden",
    pointerEvents: "none",
    opacity: 0.72,
  },
  motionTrack: {
    position: "absolute",
    left: "-10%",
    width: "120%",
    height: 1,
    background: `linear-gradient(90deg, transparent, ${C.accent}55, transparent)`,
    transform: "rotate(-12deg)",
  },
  motionTrackTop: {
    top: "24%",
    animation: "trackSweep 8s ease-in-out infinite",
  },
  motionTrackBottom: {
    top: "74%",
    animation: "trackSweep 11s ease-in-out -3s infinite reverse",
  },
  motionText: {
    position: "absolute",
    color: C.textSec,
    fontFamily: mono,
    fontSize: 10,
    fontWeight: 500,
    letterSpacing: "0.22em",
    opacity: 0.55,
    whiteSpace: "nowrap",
  },
  motionTextOne: {
    top: "20%",
    left: "8%",
    animation: "textDrift 13s ease-in-out infinite",
  },
  motionTextTwo: {
    top: "32%",
    right: "7%",
    animation: "textDrift 16s ease-in-out -5s infinite reverse",
  },
  motionTextThree: {
    bottom: "20%",
    left: "18%",
    animation: "textDrift 15s ease-in-out -8s infinite",
  },
  motionRing: {
    position: "absolute",
    width: 360,
    height: 360,
    border: `1px solid ${C.border}`,
    borderRadius: "50%",
    opacity: 0.35,
    left: "50%",
    top: "50%",
    transform: "translate(-50%, -50%) rotateX(62deg) rotateZ(-18deg)",
    animation: "ringTurn 18s linear infinite",
  },
  motionRingInner: {
    width: 220,
    height: 220,
    animationDuration: "12s",
    animationDirection: "reverse",
  },
  welcomeCard: {
    width: "min(100%, 560px)",
    textAlign: "center",
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 16,
    boxShadow: `0 24px 70px ${C.bg}99`,
    padding: "42px 48px 48px",
    position: "relative",
    zIndex: 1,
  },
  welcomeTitle: {
    fontSize: 30,
    fontWeight: 700,
    letterSpacing: "-0.04em",
    margin: "0 0 10px",
    color: C.textPri,
  },
  welcomeDesc: {
    color: C.textMid,
    fontSize: 14,
    lineHeight: 1.7,
    margin: "0 auto 28px",
    maxWidth: 430,
  },
  workspace: {
    display: "flex",
    flex: 1,
    animation: "workspaceReveal 800ms cubic-bezier(0.2, 0.85, 0.25, 1) both",
    transformOrigin: "center top",
  },
  uploadZone: (dragging) => ({
    border: `1.5px dashed ${dragging ? C.accent : C.border}`,
    borderRadius: 10,
    padding: "28px 16px",
    textAlign: "center",
    cursor: "pointer",
    background: dragging ? C.accentGlow : "transparent",
    transition: "all 0.2s",
  }),
  uploadIcon: { fontSize: 28, marginBottom: 10 },
  uploadLabel: { fontSize: 13, color: C.textMid, lineHeight: 1.6 },
  uploadBtn: {
    marginTop: 14,
    width: "100%",
    padding: "10px 0",
    background: C.accent,
    color: "#fff",
    border: "none",
    borderRadius: 7,
    fontFamily: sans,
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    letterSpacing: "0.01em",
  },
  fileName: {
    marginTop: 10,
    fontFamily: mono,
    fontSize: 11,
    color: C.green,
    wordBreak: "break-all",
  },
  infoBlock: {
    background: C.surfaceHi,
    borderRadius: 8,
    padding: 14,
    fontSize: 12,
    color: C.textSec,
    lineHeight: 1.7,
    border: `1px solid ${C.border}`,
  },
  infoTitle: {
    fontSize: 11,
    fontFamily: mono,
    color: C.textMid,
    marginBottom: 8,
    letterSpacing: "0.05em",
  },
  empty: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    gap: 12,
    color: C.textSec,
  },
  emptyIcon: { fontSize: 40, opacity: 0.4 },
  emptyTitle: { fontSize: 16, fontWeight: 600, color: C.textMid },
  emptyDesc: {
    fontSize: 13,
    maxWidth: 280,
    textAlign: "center",
    lineHeight: 1.6,
  },
  loadingWrap: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    gap: 16,
  },
  loadingDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: C.accent,
    display: "inline-block",
    margin: "0 3px",
  },
  loadingText: { color: C.textMid, fontSize: 14 },
  grid6: {
    display: "grid",
    gridTemplateColumns: "repeat(6, 1fr)",
    gap: 16,
    marginBottom: 24,
  },
  grid2: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: 16,
    marginBottom: 24,
  },
  grid3: {
    display: "grid",
    gridTemplateColumns: "2fr 1fr",
    gap: 16,
    marginBottom: 24,
  },
  card: {
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 10,
    padding: 20,
    transition: "background 0.25s, border-color 0.25s",
  },
  cardTitle: {
    fontSize: 11,
    fontFamily: mono,
    color: C.textSec,
    marginBottom: 12,
    letterSpacing: "0.06em",
  },
  statValue: {
    fontSize: 26,
    fontWeight: 700,
    letterSpacing: "-0.03em",
    lineHeight: 1,
    marginBottom: 4,
  },
  statLabel: { fontSize: 12, color: C.textSec },
  tag: {
    display: "inline-block",
    background: C.surfaceHi,
    border: `1px solid ${C.border}`,
    color: C.textMid,
    fontSize: 12,
    padding: "4px 10px",
    borderRadius: 6,
    margin: "3px 3px 3px 0",
  },
  coachBox: (color) => ({
    background: color + "18",
    border: `1px solid ${color}40`,
    borderRadius: 8,
    padding: 14,
    marginBottom: 10,
  }),
  coachTitle: {
    fontSize: 11,
    fontFamily: mono,
    marginBottom: 8,
    letterSpacing: "0.05em",
  },
  coachItem: {
    fontSize: 13,
    color: C.textMid,
    lineHeight: 1.5,
    marginBottom: 6,
    paddingLeft: 14,
    position: "relative",
  },
  transcriptBox: {
    fontFamily: mono,
    fontSize: 12,
    color: C.textMid,
    lineHeight: 1.8,
    background: C.surfaceHi,
    border: `1px solid ${C.border}`,
    borderRadius: 8,
    padding: 16,
    maxHeight: 200,
    overflowY: "auto",
    whiteSpace: "pre-wrap",
  },
  talkBar: {
    height: 8,
    borderRadius: 4,
    background: C.surfaceHi,
    display: "flex",
    overflow: "hidden",
    marginBottom: 10,
  },
  talkLegend: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: 12,
    color: C.textSec,
  },
  dot: (color) => ({
    display: "inline-block",
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: color,
    marginRight: 6,
  }),
  errorBox: {
    background: "#EF444411",
    border: "1px solid #EF444433",
    borderRadius: 8,
    padding: 12,
    fontSize: 12,
    color: "#EF4444",
  },
  confidencePill: (color) => ({
    fontSize: 11,
    fontFamily: mono,
    background: C.surfaceHi,
    color: C.textSec,
    border: `1px solid ${C.border}`,
    padding: "2px 8px",
    borderRadius: 4,
  }),
  riskPill: (color) => ({
    fontSize: 11,
    fontFamily: mono,
    background: color + "18",
    color: color,
    border: `1px solid ${color}40`,
    padding: "2px 8px",
    borderRadius: 4,
  }),
});

// ── Helpers ──────────────────────────────────────────────────────
const sentimentColor = (s, C) =>
  s === "Positive" ? C.green : s === "Negative" ? C.red : C.yellow;

const scoreColor = (n, C) => (n >= 7 ? C.green : n >= 4 ? C.yellow : C.red);

const csatColor = (n, C) => (n >= 4 ? C.green : n === 3 ? C.yellow : C.red);

const riskColor = (r, C) =>
  r === "Low" ? C.green : r === "Medium" ? C.yellow : C.red;

// ── Sub-components ────────────────────────────────────────────────

function StatCard({ label, value, color, sub, S }) {
  return (
    <div style={S.card}>
      <div style={S.cardTitle}>{label}</div>
      <div style={{ ...S.statValue, color: color || S.textPri }}>{value}</div>
      {sub && <div style={S.statLabel}>{sub}</div>}
    </div>
  );
}

function LoadingPulse({ step, C }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        gap: 16,
      }}
    >
      <div>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: C.accent,
              display: "inline-block",
              margin: "0 3px",
              animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
            }}
          />
        ))}
      </div>
      <div style={{ color: C.textMid, fontSize: 14 }}>{step}</div>
      <style>{`@keyframes pulse{0%,100%{opacity:.2;transform:scale(.8)}50%{opacity:1;transform:scale(1.2)}}`}</style>
    </div>
  );
}

function Dashboard({ data, C, S }) {
  const { transcript, analysis: a } = data;
  const [showTranscript, setShowTranscript] = useState(false);

  return (
    <div>
      {/* Row 1 — 6 stat cards */}
      <div style={S.grid6}>
        <StatCard
          S={S}
          label="SENTIMENT SCORE"
          value={`${a.sentiment_score}/10`}
          color={scoreColor(a.sentiment_score, C)}
          sub="call quality"
        />
        <StatCard
          S={S}
          label="RESOLUTION"
          value={a.resolution_status}
          color={
            a.resolution_status === "Resolved"
              ? C.green
              : a.resolution_status === "Escalated"
                ? C.red
                : C.yellow
          }
          sub={a.call_type}
        />
        <StatCard
          S={S}
          label="CUSTOMER MOOD"
          value={a.customer_sentiment}
          color={sentimentColor(a.customer_sentiment, C)}
          sub="detected"
        />
        <StatCard
          S={S}
          label="AGENT MOOD"
          value={a.agent_sentiment}
          color={sentimentColor(a.agent_sentiment, C)}
          sub="detected"
        />
        <StatCard
          S={S}
          label="PREDICTED CSAT"
          value={`${a.predicted_csat?.score ?? "—"}/5`}
          color={csatColor(a.predicted_csat?.score, C)}
          sub={a.predicted_csat?.label ?? ""}
        />
        <StatCard
          S={S}
          label="FIRST CONTACT RES."
          value={a.fcr?.resolved_on_first_contact ? "Yes ✓" : "No ✗"}
          color={a.fcr?.resolved_on_first_contact ? C.green : C.red}
          sub={`callback risk: ${a.fcr?.risk_of_callback ?? "—"}`}
        />
      </div>

      {/* Row 2 — timeline + talk ratio */}
      <div style={S.grid3}>
        <div style={S.card}>
          <div style={S.cardTitle}>SENTIMENT OVER TIME</div>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={a.sentiment_timeline}>
              <XAxis
                dataKey="minute"
                tick={{ fill: C.textSec, fontSize: 11, fontFamily: mono }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => `${v}m`}
              />
              <YAxis
                domain={[0, 10]}
                tick={{ fill: C.textSec, fontSize: 11, fontFamily: mono }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: C.surfaceHi,
                  border: `1px solid ${C.border}`,
                  borderRadius: 6,
                  fontFamily: mono,
                  fontSize: 12,
                  color: C.textPri,
                }}
                formatter={(v) => [v, "Score"]}
                labelFormatter={(l) => `Minute ${l}`}
              />
              <Line
                type="monotone"
                dataKey="score"
                stroke={C.accent}
                strokeWidth={2}
                dot={{ fill: C.accent, r: 3, strokeWidth: 0 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={S.card}>
          <div style={S.cardTitle}>TALK RATIO</div>
          <div style={S.talkBar}>
            <div
              style={{
                width: `${a.talk_ratio?.agent ?? 50}%`,
                background: C.accent,
                transition: "width 0.6s",
              }}
            />
            <div
              style={{
                width: `${a.talk_ratio?.customer ?? 50}%`,
                background: C.green,
                transition: "width 0.6s",
              }}
            />
          </div>
          <div style={S.talkLegend}>
            <span>
              <span style={S.dot(C.accent)} />
              Agent {a.talk_ratio?.agent ?? 50}%
            </span>
            <span>
              <span style={S.dot(C.green)} />
              Customer {a.talk_ratio?.customer ?? 50}%
            </span>
          </div>
          <div style={{ marginTop: 20 }}>
            <div style={S.cardTitle}>KEY TOPICS</div>
            {a.key_topics.map((t, i) => (
              <span key={i} style={S.tag}>
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Row 3 — CSAT + FCR detail */}
      <div style={S.grid2}>
        {/* Predicted CSAT */}
        <div style={S.card}>
          <div style={S.cardTitle}>PREDICTED CSAT</div>
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              gap: 16,
              marginBottom: 16,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 48,
                  fontWeight: 700,
                  lineHeight: 1,
                  color: csatColor(a.predicted_csat?.score, C),
                  letterSpacing: "-0.04em",
                }}
              >
                {a.predicted_csat?.score ?? "—"}
                <span
                  style={{ fontSize: 20, color: C.textSec, fontWeight: 400 }}
                >
                  /5
                </span>
              </div>
              <div style={{ fontSize: 13, color: C.textMid, marginTop: 4 }}>
                {a.predicted_csat?.label}
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", gap: 4, marginBottom: 8 }}>
                {[1, 2, 3, 4, 5].map((i) => (
                  <span
                    key={i}
                    style={{
                      fontSize: 20,
                      color:
                        i <= (a.predicted_csat?.score ?? 0)
                          ? csatColor(a.predicted_csat?.score, C)
                          : C.border,
                    }}
                  >
                    ★
                  </span>
                ))}
              </div>
              <span style={S.confidencePill()}>
                confidence: {a.predicted_csat?.confidence ?? "—"}
              </span>
            </div>
          </div>
          <div
            style={{
              fontSize: 13,
              color: C.textSec,
              lineHeight: 1.6,
              borderTop: `1px solid ${C.border}`,
              paddingTop: 12,
            }}
          >
            {a.predicted_csat?.reasoning}
          </div>
        </div>

        {/* FCR */}
        <div style={S.card}>
          <div style={S.cardTitle}>FIRST CONTACT RESOLUTION</div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 16,
              marginBottom: 16,
            }}
          >
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: "50%",
                background: a.fcr?.resolved_on_first_contact
                  ? C.green + "22"
                  : C.red + "22",
                border: `2px solid ${a.fcr?.resolved_on_first_contact ? C.green : C.red}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 24,
                flexShrink: 0,
              }}
            >
              {a.fcr?.resolved_on_first_contact ? "✓" : "✗"}
            </div>
            <div>
              <div
                style={{
                  fontSize: 17,
                  fontWeight: 600,
                  color: a.fcr?.resolved_on_first_contact ? C.green : C.red,
                  marginBottom: 6,
                }}
              >
                {a.fcr?.resolved_on_first_contact
                  ? "Resolved First Contact"
                  : "Not Resolved"}
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <span style={S.riskPill(riskColor(a.fcr?.risk_of_callback, C))}>
                  callback risk: {a.fcr?.risk_of_callback ?? "—"}
                </span>
                <span style={S.confidencePill()}>
                  confidence: {a.fcr?.confidence ?? "—"}
                </span>
              </div>
            </div>
          </div>
          <div
            style={{
              fontSize: 13,
              color: C.textSec,
              lineHeight: 1.6,
              borderTop: `1px solid ${C.border}`,
              paddingTop: 12,
            }}
          >
            {a.fcr?.reasoning}
          </div>
        </div>
      </div>

      {/* Row 4 — summary + coaching */}
      <div style={S.grid2}>
        <div style={S.card}>
          <div style={S.cardTitle}>CALL SUMMARY</div>
          <p
            style={{
              fontSize: 14,
              color: C.textMid,
              lineHeight: 1.7,
              margin: 0,
            }}
          >
            {a.call_summary}
          </p>
          <div style={{ marginTop: 20 }}>
            <div style={S.cardTitle}>COACHING NOTE</div>
            <p
              style={{
                fontSize: 13,
                color: C.textSec,
                lineHeight: 1.7,
                margin: 0,
              }}
            >
              {a.coaching_note}
            </p>
          </div>
        </div>

        <div style={S.card}>
          <div style={S.cardTitle}>AGENT PERFORMANCE</div>
          <div style={S.coachBox(C.green)}>
            <div style={{ ...S.coachTitle, color: C.green }}>✓ STRENGTHS</div>
            {a.agent_strengths.map((s, i) => (
              <div key={i} style={S.coachItem}>
                <span style={{ position: "absolute", left: 0, color: C.green }}>
                  ›
                </span>
                {s}
              </div>
            ))}
          </div>
          <div style={S.coachBox(C.yellow)}>
            <div style={{ ...S.coachTitle, color: C.yellow }}>⚠ IMPROVE</div>
            {a.agent_improvements.map((s, i) => (
              <div key={i} style={S.coachItem}>
                <span
                  style={{ position: "absolute", left: 0, color: C.yellow }}
                >
                  ›
                </span>
                {s}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 5 — transcript */}
      <div style={S.card}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            cursor: "pointer",
          }}
          onClick={() => setShowTranscript(!showTranscript)}
        >
          <div style={S.cardTitle}>TRANSCRIPT</div>
          <span style={{ fontSize: 12, color: C.accent, fontFamily: mono }}>
            {showTranscript ? "[ hide ]" : "[ show ]"}
          </span>
        </div>
        {showTranscript && <div style={S.transcriptBox}>{transcript}</div>}
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────
export default function App() {
  const [isDark, setIsDark] = useState(true);
  const C = isDark ? DARK : LIGHT;
  const S = makeStyles(C);

  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef();

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    setResult(null);
    setError(null);
  };
  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      setLoadingStep("Transcribing audio with Whisper...");
      await new Promise((r) => setTimeout(r, 1200));
      setLoadingStep("Analyzing sentiment and topics...");
      const res = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setLoadingStep("Building dashboard...");
      await new Promise((r) => setTimeout(r, 400));
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={S.app}>
      {/* Topbar */}
      <header style={S.topbar}>
        <div style={S.logo}>
          <span style={S.logoAccent}>Call</span>IQ
        </div>
        <div style={S.topbarRight}>
          <span style={{ fontSize: 12, color: C.textSec, fontFamily: mono }}>
            powered by groq
          </span>
          <span style={S.badge}>DEMO</span>
          {/* Theme toggle */}
          <div style={S.themeToggle} onClick={() => setIsDark(!isDark)}>
            <span>{C.toggleIcon}</span>
            <span>{C.toggleLabel}</span>
          </div>
        </div>
      </header>

      <style>{`@keyframes workspaceReveal{0%{opacity:0;transform:translate3d(0,24px,-80px) rotateX(7deg)}100%{opacity:1;transform:translate3d(0,0,0) rotateX(0)}}@keyframes trackSweep{0%,100%{opacity:.25;transform:translateX(-3%) rotate(-12deg)}50%{opacity:.8;transform:translateX(3%) rotate(-12deg)}}@keyframes textDrift{0%,100%{transform:translate3d(0,0,0);opacity:.25}50%{transform:translate3d(24px,-10px,0);opacity:.7}}@keyframes ringTurn{from{transform:translate(-50%,-50%) rotateX(62deg) rotateZ(-18deg)}to{transform:translate(-50%,-50%) rotateX(62deg) rotateZ(342deg)}}@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important}}@media (max-width:600px){.welcome-card{padding:32px 20px 36px!important}}`}</style>

      {!file ? (
        <main style={S.welcome}>
          <div style={S.welcomeBackdrop} aria-hidden="true">
            <div style={{ ...S.motionTrack, ...S.motionTrackTop }} />
            <div style={{ ...S.motionTrack, ...S.motionTrackBottom }} />
            <div style={{ ...S.motionRing, ...S.motionRingInner }} />
            <div style={S.motionRing} />
            <span style={{ ...S.motionText, ...S.motionTextOne }}>
              VOICE / SIGNAL / INSIGHT
            </span>
            <span style={{ ...S.motionText, ...S.motionTextTwo }}>
              CALL_001 // READY
            </span>
            <span style={{ ...S.motionText, ...S.motionTextThree }}>
              TRANSCRIBE → ANALYZE → IMPROVE
            </span>
          </div>
          <div style={S.welcomeCard}>
            <div style={S.emptyIcon}>📞</div>
            <h1 style={S.welcomeTitle}>Welcome to CallIQ</h1>
            <p style={S.welcomeDesc}>
              Turn your first call recording into clear customer signals,
              coaching moments, and quality insights.
            </p>
            <div
              style={S.uploadZone(dragging)}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current.click()}
            >
              <div style={S.uploadIcon}>🎙</div>
              <div style={S.uploadLabel}>
                Drop your first audio clip here
                <br />
                <span style={{ color: C.textSec, fontSize: 11 }}>
                  .mp3 · .wav · .m4a supported
                </span>
              </div>
              <input
                ref={inputRef}
                type="file"
                accept=".mp3,.wav,.m4a"
                style={{ display: "none" }}
                onChange={(e) => handleFile(e.target.files[0])}
              />
            </div>
          </div>
        </main>
      ) : (
        <div style={S.workspace}>
          <div style={S.body}>
            {/* Sidebar */}
            <aside style={S.sidebar}>
              <div>
                <div
                  style={{
                    fontSize: 12,
                    color: C.textSec,
                    marginBottom: 12,
                    fontFamily: mono,
                  }}
                >
                  UPLOAD RECORDING
                </div>
                <div
                  style={S.uploadZone(dragging)}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragging(true);
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => inputRef.current.click()}
                >
                  <div style={S.uploadIcon}>🎙</div>
                  <div style={S.uploadLabel}>
                    Drop a call recording here
                    <br />
                    <span style={{ color: C.textSec, fontSize: 11 }}>
                      .mp3 · .wav · .m4a supported
                    </span>
                  </div>
                  {file && <div style={S.fileName}>✓ {file.name}</div>}
                  <input
                    ref={inputRef}
                    type="file"
                    accept=".mp3,.wav,.m4a"
                    style={{ display: "none" }}
                    onChange={(e) => handleFile(e.target.files[0])}
                  />
                </div>
                <button
                  style={{
                    ...S.uploadBtn,
                    opacity: file && !loading ? 1 : 0.4,
                    cursor: file && !loading ? "pointer" : "not-allowed",
                  }}
                  onClick={handleAnalyze}
                  disabled={!file || loading}
                >
                  {loading ? "Analyzing..." : "Analyze Call →"}
                </button>
              </div>

              <div style={S.infoBlock}>
                <div style={S.infoTitle}>WHAT THIS DOES</div>
                Transcribes your call with Whisper, then runs AI to extract
                sentiment, key topics, CSAT prediction, FCR status, and agent
                coaching — in seconds.
              </div>

              <div style={S.infoBlock}>
                <div style={S.infoTitle}>POWERED BY</div>
                {[
                  "Groq Whisper — transcription",
                  "GPT-OSS 120B — analysis",
                  "React + Recharts — UI",
                  "Flask — API backend",
                ].map((t) => (
                  <div
                    key={t}
                    style={{ fontSize: 12, color: C.textSec, marginBottom: 2 }}
                  >
                    <span style={{ color: C.accent }}>›</span> {t}
                  </div>
                ))}
              </div>

              {error && <div style={S.errorBox}>⚠ {error}</div>}
            </aside>

            {/* Main */}
            <main style={S.main}>
              {loading && <LoadingPulse step={loadingStep} C={C} />}
              {!loading && !result && (
                <div style={S.empty}>
                  <div style={S.emptyIcon}>📞</div>
                  <div style={S.emptyTitle}>No call analyzed yet</div>
                  <div style={S.emptyDesc}>
                    Upload a call recording from the sidebar to get AI-powered
                    insights on sentiment, coaching, CSAT, and FCR.
                  </div>
                </div>
              )}
              {!loading && result && <Dashboard data={result} C={C} S={S} />}
            </main>
          </div>
        </div>
      )}
    </div>
  );
}
