import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
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
# SIDEBAR ROADMAP
# -----------------------------
with st.sidebar:
    if st.button("Show 30-Day Red Team AI Roadmap"):
        st.markdown("""
## 30-Day Red Team AI Roadmap

### Day 1
- Write ML assumptions
- Write LLM assumptions
- Write evaluation failures

### Days 2 to 6
Core adversarial ML
- Break NLP model using TextAttack
- Insert backdoor trigger
- Robustness evaluation
Resources:
- TextAttack
- TrojAI
- Robustness Gym

### Days 7 to 11
Data poisoning and leakage
- Poison 1 to 3 percent of data
- Introduce train test leakage
- Shortcut learning demo
Resources:
- TrojAI
- Adversarial ML book

### Days 12 to 17
LLM red teaming
- Prompt injection
- Indirect injection
- Safety boundary mapping
Resources:
- Lakera Labs
- Garak
- OWASP LLM Top 10

### Days 18 to 22
Multimodal attacks
- CLIP backdoor
- Cross modal confusion
Resources:
- BadCLIP

### Days 23 to 26
Threat modeling
- Define attacker
- Break defenses

### Days 27 to 29
Original contribution
- New metric or attack

### Day 30
Final red team report
""")

# -----------------------------
# USER SETUP
# -----------------------------
user = c.execute("SELECT * FROM user WHERE id=1").fetchone()

if user is None:
    st.title("Initialize Red Team AI Profile")

    name = st.text_input("Name")
    redteam_total = st.number_input("Total Red Team AI Units", min_value=1)
    dl_total = st.number_input("Total DL Theory Pages", min_value=1)
    target_projects = st.number_input("Target Projects", min_value=1)

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
    "Execution Notes",
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
    fj_system = st.text_input("System or Model")

with fj_col2:
    fj_type = st.selectbox(
        "Failure Type",
        [
            "Prompt Injection",
            "Backdoor",
            "Data Leakage",
            "Shortcut Learning",
            "Robustness Failure",
            "Evaluation Bug",
            "Other"
        ]
    )

with fj_col3:
    fj_desc = st.text_input("Failure Description")

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

if execution_score < 33:
    st.error("RED ZONE")
elif execution_score < 66:
    st.warning("YELLOW ZONE")
else:
    st.success("GREEN ZONE")

# -----------------------------
# STREAK
# -----------------------------
df["active"] = (df[["redteam_units", "dl_pages", "projects"]].sum(axis=1) > 0)
streak = 0
for a in reversed(df["active"].tolist()):
    if a:
        streak += 1
    else:
        break

st.metric("Current Streak (Days)", streak)

# -----------------------------
# VISUALS
# -----------------------------
st.subheader("Velocity Over Time")

fig1 = px.line(df, x="day", y=["redteam_units", "dl_pages"])
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.bar(df, x="day", y="projects")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# FAILURE ANALYTICS
# -----------------------------
st.subheader("Failure Analytics")

fj_df = pd.read_sql("SELECT * FROM failure_journal ORDER BY id DESC", conn)

if not fj_df.empty:
    fig3 = px.histogram(fj_df, x="failure_type")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No failures logged yet")

# -----------------------------
# FINAL VERDICT
# -----------------------------
proj_redteam_days = redteam_burn / redteam_velocity if redteam_velocity > 0 else float("inf")
proj_dl_days = dl_burn / dl_velocity if dl_velocity > 0 else float("inf")
proj_project_days = project_burn / project_velocity if project_velocity > 0 else float("inf")

st.subheader("System Verdict")

if max(proj_redteam_days, proj_dl_days, proj_project_days) > 30:
    st.error("SYSTEM VERDICT: DEADLINE WILL BE MISSED")
else:
    st.success("SYSTEM VERDICT: DEADLINE ACHIEVABLE")
