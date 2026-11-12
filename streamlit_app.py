"""Live Accountability Dashboard (Streamlit).

Companion app for a 20-minute talk on
"Building a Culture of Accountability and Operational Excellence".

Tabs
1. Live poll          - audience votes from their phones; results refresh every few seconds.
2. Why lapses add up  - chance a whole job is done right = (chance per step) ** steps.
3. KPI scorecard      - one owner, one due date, one status per task (simulated data).
4. Feedback           - post-talk feedback and an automatic summary.

All operational data is simulated. Votes and feedback are anonymous and held in memory only.
"""

from __future__ import annotations

import re
import threading
from collections import Counter
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BLUE, GREY, GOLD, RED, GREEN = "#0b4f6c", "#b9c4cc", "#c58b1a", "#b23a3a", "#2e7d4f"
POLL_OPTIONS = ["Whose fault is this?", "What can I do about it?"]
HABITS = [
    "Own the outcome, not only the task",
    "Confirm what 'done' looks like and by when",
    "Track 2-3 numbers on my own work",
    "Flag risks early, with a suggested fix",
    "Close the loop and note one lesson",
]
STOP = set("""a an the and or but if then so to of in on for with at by from is are was were be been
i me my we our you your it this that these those will would can could should do did done not no
more less very just also about into than as have has had get got make one thing things""".split())

st.set_page_config(page_title="Accountability Dashboard", page_icon="📊", layout="wide")


# ------------------------------------------------------------------ shared store
@st.cache_resource
def store() -> dict:
    """One in-memory store shared by every visitor while the app is running."""
    return {"lock": threading.Lock(), "poll": {o: 0 for o in POLL_OPTIONS}, "feedback": []}


S = store()


def styled(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=45, r=15, t=50, b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial", size=14, color="#1d2430"),
    )
    return fig


# ------------------------------------------------------------------ header
st.title("Accountability & Operational Excellence: Live Dashboard")
st.caption(
    "Companion app for the talk *Building a Culture of Accountability and Operational Excellence*. "
    "All operational figures are simulated; votes and feedback are anonymous."
)

tab_poll, tab_rel, tab_kpi, tab_fb = st.tabs(
    ["1 · Live poll", "2 · Why small lapses add up", "3 · KPI scorecard", "4 · Feedback"]
)

# ------------------------------------------------------------------ 1. poll
with tab_poll:
    st.markdown("**Think of the last time something went wrong. What was your first thought?**")
    choice = st.radio("Your answer", POLL_OPTIONS, index=None, key="poll_choice")
    if st.button("Vote", type="primary", key="vote_btn"):
        if choice is None:
            st.warning("Please pick an answer first.")
        elif st.session_state.get("voted"):
            st.info("Thank you, your vote is already counted.")
        else:
            with S["lock"]:
                S["poll"][choice] += 1
            st.session_state["voted"] = True
            st.success("Thank you, your vote is counted.")

    @st.fragment(run_every=3)
    def poll_results():
        with S["lock"]:
            counts = dict(S["poll"])
        total = sum(counts.values())
        text = [f"{v} ({v / total:.0%})" if total else "0" for v in counts.values()]
        fig = go.Figure(go.Bar(
            x=list(counts.values()), y=list(counts.keys()), orientation="h",
            text=text, textposition="auto", marker_color=[GREY, BLUE],
        ))
        fig.update_layout(
            title=f"When something goes wrong, my first thought is... "
                  f"({total} vote{'' if total == 1 else 's'})",
            xaxis=dict(visible=False), yaxis=dict(autorange="reversed", automargin=True, ticklabelstandoff=8),
        )
        st.plotly_chart(styled(fig, 280), width="stretch", theme=None)
        st.caption("Results refresh every 3 seconds.")

    poll_results()

# ------------------------------------------------------------------ 2. reliability
with tab_rel:
    c1, c2 = st.columns(2)
    steps = c1.slider("Steps in the job", 1, 50, 20)
    pct = c2.slider("Chance each step is done right (%)", 90.0, 99.9, 99.0, 0.1)
    p = pct / 100
    success = p ** steps
    st.markdown(f"### {success:.0%} chance the whole job is done right")
    st.markdown(
        f"A job with **{steps} steps**, each done right **{pct:.1f}%** of the time, goes wrong in about "
        f"**{(1 - success) * 100:.0f} of every 100 jobs**. Small lapses add up. "
        "Excellence is getting every step right, every time."
    )
    xs = list(range(1, 51))
    fig = go.Figure()
    for ref, colour in [(95.0, RED), (99.0, GOLD), (99.9, GREEN)]:
        fig.add_trace(go.Scatter(x=xs, y=[(ref / 100) ** s * 100 for s in xs], mode="lines",
                                 name=f"{ref}% per step", line=dict(color=colour, width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=xs, y=[p ** s * 100 for s in xs], mode="lines",
                             name=f"Your setting: {pct:.1f}% per step", line=dict(color=BLUE, width=4)))
    fig.add_trace(go.Scatter(x=[steps], y=[success * 100], mode="markers+text", showlegend=False,
                             marker=dict(size=14, color=BLUE), text=[f"{success:.0%}"],
                             textposition="top right"))
    fig.update_layout(title="Chance the whole job is done right", xaxis_title="Number of steps in the job",
                      yaxis_title="%", yaxis=dict(range=[0, 105]), legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(styled(fig, 400), width="stretch", theme=None)

# ------------------------------------------------------------------ 3. scorecard
with tab_kpi:
    st.markdown("**Make performance visible:** one owner, one due date, one status for every task.")
    today = date.today()
    rows = [
        ("Pre-job safety briefing, Site A", "Field Supervisor", -1, "Done"),
        ("Equipment inspection log update", "Maintenance Lead", -2, "Done"),
        ("Client weekly operations report", "Operations Analyst", 0, "In progress"),
        ("Permit-to-work renewal", "HSE Officer", 1, "In progress"),
        ("Spare parts reorder", "Procurement Officer", -3, "Overdue"),
        ("Crew rotation schedule", "Operations Coordinator", 3, "Not started"),
        ("Near-miss report review", "HSE Officer", -1, "Done"),
        ("Invoice reconciliation", "Finance Officer", -4, "Overdue"),
        ("Vehicle maintenance booking", "Logistics Officer", 2, "In progress"),
        ("Training attendance record", "HR Officer", -2, "Done"),
        ("Tool calibration certificate", "Maintenance Lead", 5, "Not started"),
        ("Lessons-learned note, last job", "Project Engineer", -1, "Done"),
    ]
    df = pd.DataFrame(rows, columns=["Task", "Owner", "due_offset", "Status"])
    df["Due"] = [(today + timedelta(days=int(d))).strftime("%d %b") for d in df["due_offset"]]
    df["Days overdue"] = [max(0, -int(d)) if s == "Overdue" else 0
                          for d, s in zip(df["due_offset"], df["Status"])]
    counts = df["Status"].value_counts().reindex(["Done", "In progress", "Not started", "Overdue"]).fillna(0)
    weeks = [f"W{i}" for i in range(1, 9)]
    on_time = [71, 74, 73, 78, 82, 81, 86, 89]
    checks = [80, 84, 85, 88, 91, 93, 95, 96]

    m = st.columns(5)
    m[0].metric("Tasks", len(df))
    m[1].metric("Done", int(counts["Done"]))
    m[2].metric("Overdue", int(counts["Overdue"]))
    m[3].metric("Pre-job checks (this week)", f"{checks[-1]}%", f"{checks[-1] - checks[-2]} pts")
    m[4].metric("Tasks on time (this week)", f"{on_time[-1]}%", f"{on_time[-1] - on_time[-2]} pts")

    g1, g2 = st.columns(2)
    bar = go.Figure(go.Bar(x=counts.index, y=counts.values, text=counts.values.astype(int),
                           textposition="auto", marker_color=[GREEN, BLUE, GREY, RED]))
    bar.update_layout(title="Tasks by status (every task has one owner)", yaxis=dict(visible=False))
    g1.plotly_chart(styled(bar, 320), width="stretch", theme=None)
    trend = go.Figure()
    trend.add_trace(go.Scatter(x=weeks, y=checks, name="Leading: pre-job checks done (%)",
                               mode="lines+markers", line=dict(color=GREEN, width=3)))
    trend.add_trace(go.Scatter(x=weeks, y=on_time, name="Lagging: tasks closed on time (%)",
                               mode="lines+markers", line=dict(color=BLUE, width=3)))
    trend.update_layout(title="Leading vs lagging measures, last 8 weeks", yaxis=dict(range=[60, 100]),
                        legend=dict(orientation="h", y=-0.25))
    g2.plotly_chart(styled(trend, 320), width="stretch", theme=None)

    def highlight(row):
        colour = "background-color: #f6dede" if row["Status"] == "Overdue" else ""
        return [colour] * len(row)

    st.dataframe(df[["Task", "Owner", "Due", "Status", "Days overdue"]].style.apply(highlight, axis=1),
                 hide_index=True, width="stretch")
    st.caption("Simulated data, for illustration only.")

# ------------------------------------------------------------------ 4. feedback
with tab_fb:
    with st.form("feedback", clear_on_submit=True):
        rating = st.slider("How useful was this talk? (1 = not useful, 5 = very useful)", 1, 5, 4)
        habit = st.radio("Which habit will you start on Monday?", HABITS, index=None)
        comment = st.text_area("One thing you will do differently (optional)", max_chars=500)
        sent = st.form_submit_button("Send feedback", type="primary")
    if sent:
        if st.session_state.get("fb_sent"):
            st.info("Thank you, your feedback is already recorded.")
        elif habit is None:
            st.warning("Please choose the habit you will start.")
        else:
            with S["lock"]:
                S["feedback"].append({"rating": rating, "habit": habit, "comment": comment or ""})
            st.session_state["fb_sent"] = True
            st.success("Thank you for your feedback.")

    st.divider()
    st.markdown("**Summary for the organiser**")
    if st.button("Refresh summary"):
        st.session_state["show_summary"] = True
    if st.session_state.get("show_summary"):
        with S["lock"]:
            fb = list(S["feedback"])
        if not fb:
            st.info("No feedback yet.")
        else:
            fdf = pd.DataFrame(fb)
            n = len(fdf)
            st.markdown(
                f"### {n} response{'' if n == 1 else 's'} · average usefulness {fdf['rating'].mean():.1f} / 5 · "
                f"{(fdf['rating'] >= 4).mean():.0%} rated it 4 or 5"
            )
            habits = fdf["habit"].value_counts().reindex(HABITS).fillna(0)
            hfig = go.Figure(go.Bar(x=habits.values, y=habits.index, orientation="h", marker_color=BLUE,
                                    text=habits.values.astype(int), textposition="auto"))
            hfig.update_layout(title="Habit people will start", xaxis=dict(visible=False),
                               yaxis=dict(autorange="reversed", automargin=True, ticklabelstandoff=8))
            st.plotly_chart(styled(hfig, 300), width="stretch", theme=None)
            words = Counter(w for c in fdf["comment"] for w in re.findall(r"[a-z']+", c.lower())
                            if len(w) > 2 and w not in STOP)
            st.markdown("**Most-mentioned words in comments**")
            st.dataframe(pd.DataFrame(words.most_common(8), columns=["Word", "Mentions"]), hide_index=True)

    with st.expander("Admin"):
        code = st.text_input("Admin code", type="password")
        if st.button("Clear poll and feedback"):
            try:
                admin = st.secrets.get("ADMIN_CODE", "")
            except Exception:  # no secrets configured
                admin = ""
            if admin and code == admin:
                with S["lock"]:
                    S["poll"] = {o: 0 for o in POLL_OPTIONS}
                    S["feedback"] = []
                st.success("Poll and feedback cleared.")
            else:
                st.error("Reset not allowed.")
