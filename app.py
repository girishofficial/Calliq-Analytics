import streamlit as st
import os
import tempfile
import plotly.graph_objects as go
from transcriber import transcribe_audio
from analyzer import analyze_call

# --- Page config ---
st.set_page_config(
    page_title="Signal Desk | Call Analytics",
    page_icon="◒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root {
        --ink: #17252b;
        --muted: #6d7d82;
        --canvas: #f4f7f6;
        --paper: #ffffff;
        --line: #e0e8e6;
        --coral: #ee735f;
        --teal: #277f7b;
        --mint: #dcefea;
    }

    .stApp { background: var(--canvas); color: var(--ink); }
    .block-container { max-width: 1240px; padding: 2.5rem 3.5rem 4rem; }
    h1, h2, h3, h4, p, label, .stMarkdown { font-family: 'DM Sans', sans-serif; }
    h1, h2, h3, h4 { color: var(--ink); font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em; }
    h1 { font-size: clamp(2.2rem, 4vw, 4rem); line-height: 1.02; margin: 0; }
    h2 { font-size: 1.45rem; margin: 0; }
    h3 { font-size: 1.05rem; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: var(--ink); }
    [data-testid="stSidebar"] * { color: #eef7f4; }
    .eyebrow { color: var(--coral); font-size: .75rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; margin-bottom: .9rem; }
    .subtitle { color: var(--muted); font-size: 1.05rem; line-height: 1.55; max-width: 610px; margin: 1rem 0 0; }
    .topbar { align-items: center; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; margin-bottom: 4.5rem; padding-bottom: 1rem; }
    .brand { align-items: center; display: flex; gap: .7rem; font-family: 'Space Grotesk', sans-serif; font-size: 1.05rem; font-weight: 700; }
    .brand-mark { align-items: center; background: var(--coral); border-radius: 9px; color: white; display: flex; font-size: 1.05rem; height: 31px; justify-content: center; width: 31px; }
    .status { align-items: center; color: var(--muted); display: flex; font-size: .83rem; gap: .45rem; }
    .status-dot { background: #47ad81; border-radius: 50%; height: 7px; width: 7px; }
    .hero { margin-bottom: 2.3rem; }
    .panel { background: var(--paper); border: 1px solid var(--line); border-radius: 16px; padding: 1.4rem 1.5rem; }
    .panel-label { color: var(--muted); font-size: .73rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
    .upload-panel { background: var(--ink); border: 0; color: white; min-height: 205px; padding: 1.8rem; }
    .upload-panel h2, .upload-panel .panel-label { color: white; }
    .upload-panel .panel-label { color: #97b3af; }
    .upload-copy { color: #a9bfbc; font-size: .9rem; margin: .5rem 0 1.1rem; }
    [data-testid="stFileUploaderDropzone"] { background: #25383d; border: 1px dashed #52726f; border-radius: 11px; }
    [data-testid="stFileUploaderDropzone"] small { color: #a9bfbc; }
    .metric-card { background: var(--paper); border: 1px solid var(--line); border-radius: 14px; min-height: 122px; padding: 1.15rem 1.2rem; }
    .metric-name { color: var(--muted); font-size: .78rem; font-weight: 600; }
    .metric-value { color: var(--ink); font-family: 'Space Grotesk', sans-serif; font-size: 1.55rem; font-weight: 700; margin-top: .75rem; }
    .metric-accent { color: var(--coral); }
    .section-head { align-items: end; display: flex; justify-content: space-between; margin: 2.5rem 0 1rem; }
    .section-kicker { color: var(--muted); font-size: .88rem; }
    .topic { background: var(--mint); border-radius: 999px; color: var(--teal); display: inline-block; font-size: .8rem; font-weight: 600; margin: .2rem .25rem .2rem 0; padding: .42rem .7rem; }
    .summary { color: #43565a; font-size: 1rem; line-height: 1.7; }
    .coaching { background: #fff2e9; border-left: 4px solid var(--coral); border-radius: 0 12px 12px 0; color: #62483d; line-height: 1.6; padding: 1rem 1.15rem; }
    .empty-state { background: var(--paper); border: 1px solid var(--line); border-radius: 18px; margin-top: 1.5rem; padding: 3.3rem; text-align: center; }
    .empty-icon { color: var(--coral); font-family: 'Space Grotesk', sans-serif; font-size: 3.5rem; font-weight: 700; }
    .empty-state p { color: var(--muted); margin: .5rem auto 0; max-width: 440px; }
    .stButton > button { background: var(--coral); border: 0; border-radius: 9px; color: white; font-weight: 700; }
    .stButton > button:hover { background: #d96151; color: white; }
    [data-testid="stExpander"] { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; }
    @media (max-width: 700px) { .block-container { padding: 1.4rem 1rem 3rem; } .topbar { margin-bottom: 2.5rem; } .status { display: none; } }
    </style>
    """,
    unsafe_allow_html=True,
)

def metric_card(label: str, value: str, accent: bool = False) -> None:
    value_class = "metric-value metric-accent" if accent else "metric-value"
    st.markdown(
        f'<div class="metric-card"><div class="metric-name">{label}</div>'
        f'<div class="{value_class}">{value}</div></div>',
        unsafe_allow_html=True,
    )


def render_gauge(score: float) -> None:
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"font": {"family": "Space Grotesk", "size": 42, "color": "#17252b"}},
            gauge={
                "axis": {"range": [0, 10], "tickwidth": 0, "tickcolor": "#ffffff"},
                "bar": {"color": "#ee735f", "thickness": .72},
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 4], "color": "#f7d8d0"},
                    {"range": [4, 7], "color": "#f7edcf"},
                    {"range": [7, 10], "color": "#dcefea"},
                ],
            },
        )
    )
    figure.update_layout(height=220, margin=dict(t=16, b=0, l=16, r=16), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def render_analysis(transcript: str, analysis: dict) -> None:
    st.markdown('<div class="section-head"><h2>Call overview</h2><span class="section-kicker">AI-generated quality signals</span></div>', unsafe_allow_html=True)
    metrics = st.columns(4)
    with metrics[0]:
        metric_card("Overall sentiment", analysis["overall_sentiment"], accent=True)
    with metrics[1]:
        metric_card("Sentiment score", f'{analysis["sentiment_score"]} / 10')
    with metrics[2]:
        metric_card("Resolution", analysis["resolution_status"])
    with metrics[3]:
        metric_card("Call type", analysis["call_type"])

    st.markdown('<div class="section-head"><h2>Conversation readout</h2></div>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.15], gap="large")
    with left:
        st.markdown('<div class="panel"><div class="panel-label">Sentiment signal</div>', unsafe_allow_html=True)
        render_gauge(analysis["sentiment_score"])
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="panel-label">Call summary</div><h3>What happened</h3>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary">{analysis["call_summary"]}</div><br><div class="panel-label">Key topics</div>', unsafe_allow_html=True)
        st.markdown("".join(f'<span class="topic">{topic}</span>' for topic in analysis["key_topics"]), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head"><h2>Agent coaching</h2><span class="section-kicker">Practical feedback for the next call</span></div>', unsafe_allow_html=True)
    strengths, improvements = st.columns(2, gap="large")
    with strengths:
        st.markdown('<div class="panel"><div class="panel-label">What worked</div><h3>Strengths</h3>', unsafe_allow_html=True)
        for strength in analysis["agent_strengths"]:
            st.success(strength)
        st.markdown('</div>', unsafe_allow_html=True)
    with improvements:
        st.markdown('<div class="panel"><div class="panel-label">Next opportunity</div><h3>Areas to improve</h3>', unsafe_allow_html=True)
        for improvement in analysis["agent_improvements"]:
            st.warning(improvement)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head"><h2>Coaching note</h2></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="coaching">{analysis["coaching_note"]}</div>', unsafe_allow_html=True)
    with st.expander("View full transcript"):
        st.write(transcript)


st.markdown(
    '<div class="topbar"><div class="brand"><span class="brand-mark">◒</span>Signal Desk</div>'
    '<div class="status"><span class="status-dot"></span>Workspace ready</div></div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="hero"><div class="eyebrow">Conversation intelligence</div><h1>Make every call<br>count.</h1><p class="subtitle">Turn recordings into clear coaching moments, customer signals, and decisions your team can act on.</p></div>', unsafe_allow_html=True)

st.markdown('<div class="panel upload-panel"><div class="panel-label">Start with a recording</div><h2>Analyze a customer conversation</h2><div class="upload-copy">Upload an audio file to generate a transcript and quality readout.</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Audio recording", type=["mp3", "wav", "m4a"], label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    st.markdown(f'<div class="section-head"><h2>{uploaded_file.name}</h2><span class="section-kicker">Ready to analyze</span></div>', unsafe_allow_html=True)
    st.audio(uploaded_file, format=f"audio/{os.path.splitext(uploaded_file.name)[1].lstrip('.')}")
    if st.button("Run call analysis", type="primary"):
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(uploaded_file.getvalue())
            temporary_path = temporary_file.name
        try:
            with st.spinner("Transcribing and analyzing your call..."):
                transcript = transcribe_audio(temporary_path)
                analysis = analyze_call(transcript)
            render_analysis(transcript, analysis)
        finally:
            os.unlink(temporary_path)
else:
    st.markdown('<div class="empty-state"><div class="empty-icon">◒</div><h2>Your call workspace is ready</h2><p>Drop an MP3, WAV, or M4A recording above to see sentiment, resolution, topics, and coaching feedback in one place.</p></div>', unsafe_allow_html=True)