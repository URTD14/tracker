import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, timedelta
import plotly.express as px

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="Red Team AI Execution Dashboard",
    layout="wide"
)

DB_PATH = "execution.db"

# -----------------------------
# DB INIT
# -----------------------------
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS progress (
    day TEXT PRIMARY KEY,
    redteam_units INTEGER,
    dl_pages INTEGER,
    projects INTEGER,
    notes TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    name TEXT,
    start_date TEXT,
    redteam_total INTEGER,
    dl_total INTEGER,
    target_projects INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS failure_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT,
    system TEXT,
    failure_type TEXT,
    description TEXT
)
""")

conn.commit()

# -----------------------------
# USER SETUP
# -----------------------------
user = c.execute("SELECT * FROM user WHERE id=1").fetchone()

if user is None:
    st.title("Initialize Red Team AI Profile")

    name = st.text_input("Name")
    redteam_total = st.number_input("Total Red Team AI Units (30 Days)", min_value=1)
    dl_total = st.number_input("Total Deep Learning Theory Pages", min_value=1)
    target_projects = st.number_input("Target Total Projects", min_value=1)

    if st.button("Lock In"):
        c.execute("""
        INSERT INTO user VALUES (1, ?, ?, ?, ?, ?)
        """, (
            name,
            date.today().isoformat(),
            redteam_total,
            dl_total,
            target_projects
        ))
        conn.commit()
        st.rerun()

    st.stop()

_, name, start_date, redteam_total, dl_total, target_projects = user
start_date = date.fromisoformat(start_date)

# -----------------------------
# INPUT TODAY
# -----------------------------
st.title(f"Red Team AI Execution Dashboard | {name}")

today = date.today().isoformat()
existing = c.execute("SELECT * FROM progress WHERE day=?", (today,)).fetchone()

st.subheader("Log Today")

col1, col2, col3 = st.columns(3)

with col1:
    redteam_today = st.number_input(
        "Red Team AI Units Today",
        min_value=0,
        value=existing[1] if existing else 0
    )

with col2:
    dl_today = st.number_input(
        "DL Theory Pages Today",
        min_value=0,
        value=existing[2] if existing else 0
    )

with col3:
    projects_today = st.number_input(
        "Projects Finished Today",
        min_value=0,
        value=existing[3] if existing else 0
    )

notes_today = st.text_area(
    "Execution Notes / Attacks / Insights",
    value=existing[4] if existing else ""
)

if st.button("Commit"):
    c.execute("""
    INSERT OR REPLACE INTO progress VALUES (?, ?, ?, ?, ?)
    """, (today, redteam_today, dl_today, projects_today, notes_today))
    conn.commit()
    st.rerun()

# -----------------------------
# FAILURE JOURNAL
# -----------------------------
st.subheader("Failure Journal")

fj_col1, fj_col2, fj_col3 = st.columns(3)

with fj_col1:
    fj_system = st.text_input("System / Model Name")

with fj_col2:
    fj_type = st.selectbox(
        "Failure Type",
        ["Prompt Injection", "Backdoor", "Data Leakage", "Shortcut Learning", "Robustness Failure", "Evaluation Bug", "Other"]
    )

with fj_col3:
    fj_desc = st.text_input("Short Failure Description")

if st.button("Log Failure"):
    c.execute("""
    INSERT INTO failure_journal (day, system, failure_type, description)
    VALUES (?, ?, ?, ?)
    """, (today, fj_system, fj_type, fj_desc))
    conn.commit()
    st.success("Failure Logged")

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_sql("SELECT * FROM progress ORDER BY day", conn)
df["day"] = pd.to_datetime(df["day"])

days_elapsed = (date.today() - start_date).days + 1

# -----------------------------
# METRICS
# -----------------------------
redteam_done = df["redteam_units"].sum()
dl_done = df["dl_pages"].sum()
projects_done = df["projects"].sum()

redteam_velocity = redteam_done / max(days_elapsed, 1)
dl_velocity = dl_done / max(days_elapsed, 1)
project_velocity = projects_done / max(days_elapsed, 1)

redteam_burn = redteam_total - redteam_done
dl_burn = dl_total - dl_done
project_burn = target_projects - projects_done

# -----------------------------
# SCORE
# -----------------------------
execution_score = (
    (redteam_done / redteam_total) +
    (dl_done / dl_total) +
    (projects_done / target_projects)
) / 3 * 100

# -----------------------------
# DASHBOARD
# -----------------------------
st.subheader("Core Metrics")

m1, m2, m3, m4 = st.columns(4)

m1.metric("Red Team AI Units", f"{redteam_done}/{redteam_total}")
m2.metric("DL Theory Pages", f"{dl_done}/{dl_total}")
m3.metric("Projects", f"{projects_done}/{target_projects}")
m4.metric("Execution Score", f"{execution_score:.1f}%")

# -----------------------------
# RED ZONE
# -----------------------------
if execution_score < 33:
    st.error("RED ZONE: EXECUTION FAILURE")
elif execution_score < 66:
    st.warning("YELLOW ZONE: UNDERPERFORMANCE")
else:
    st.success("GREEN ZONE: ON TRACK")

# -----------------------------
# STREAK
# -----------------------------
df["active"] = (df[["redteam_units", "dl_pages", "projects"]].sum(axis=1) > 0)
streak = 0
for active in reversed(df["active"].tolist()):
    if active:
        streak += 1
    else:
        break

st.metric("Current Streak (Days)", streak)

# -----------------------------
# VISUALS
# -----------------------------
st.subheader("Velocity Over Time")

fig1 = px.line(df, x="day", y=["redteam_units", "dl_pages"], title="Execution Velocity")
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.bar(df, x="day", y="projects", title="Projects Completed")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# BURN RATE PROJECTION
# -----------------------------
st.subheader("Burn Rate Projection")

proj_redteam_days = redteam_burn / redteam_velocity if redteam_velocity > 0 else float("inf")
proj_dl_days = dl_burn / dl_velocity if dl_velocity > 0 else float("inf")
proj_project_days = project_burn / project_velocity if project_velocity > 0 else float("inf")

p1, p2, p3 = st.columns(3)

p1.metric("Red Team Days Remaining", f"{proj_redteam_days:.1f}")
p2.metric("DL Days Remaining", f"{proj_dl_days:.1f}")
p3.metric("Project Days Remaining", f"{proj_project_days:.1f}")

# -----------------------------
# FAILURE ANALYTICS PLUGIN
# -----------------------------
st.subheader("Failure Analytics")

fj_df = pd.read_sql("SELECT * FROM failure_journal ORDER BY id DESC", conn)

if not fj_df.empty:
    fig3 = px.histogram(fj_df, x="failure_type", title="Failure Type Distribution")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No failures logged yet")

# -----------------------------
# FINAL JUDGMENT
# -----------------------------
st.subheader("System Verdict")

if max(proj_redteam_days, proj_dl_days, proj_project_days) > 30:
    st.error("SYSTEM VERDICT: YOU WILL MISS THE DEADLINE AT CURRENT VELOCITY")
else:
    st.success("SYSTEM VERDICT: DEADLINE ACHIEVABLE AT CURRENT VELOCITY")
