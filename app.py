import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

# ================== TIMEZONE ==================
LOCAL_TZ = ZoneInfo("Asia/Kolkata")  # ✅ DEFINE HERE

# ================== CONFIG ==================
st.set_page_config(
    page_title="Time Tracking Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_FILE = "data.csv"

USERS = {
    "admin": "admin123",
    "Revathi": "revathi123",
    "Jayalakshmi": "jaya123",
    "Chithra": "chitra123",
    "Bhavani": "bhavani123",
    "Vijay": "vijay123",
}

STAGES = [
    "Analyse",
    "Configuration",
    "Add Section",
    "Extraction",
    "Self-QA",
    "QA",
    "Error Clearing",
    "QA (Error Cleared)"
]

STATUS_OPTIONS = ["In Progress", "Hold", "Dev Help", "Completed"]

# ================== SESSION ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.ib_rows = []

# ================== DATA INIT ==================
EXPECTED_COLUMNS = ["Employee", "IB", "URL", "Status", "Stage", "Action", "Time", "Date"]

if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    df.to_csv(DATA_FILE, index=False)
else:
    df = pd.read_csv(DATA_FILE)
    df.columns = df.columns.str.strip()
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NaT if col in ["Time", "Date"] else ""
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")

    if df["Time"].dt.tz is None:
        df["Time"] = df["Time"].dt.tz_localize(LOCAL_TZ)
    else:
       df["Time"] = df["Time"].dt.tz_convert(LOCAL_TZ)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df.to_csv(DATA_FILE, index=False)

# ================== LOGIN ==================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center'>⏱️ Time Tracking Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:gray'>Secure process monitoring</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 2])
    with col2:
        username = st.selectbox("Username", USERS.keys())
        password = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            if USERS.get(username) == password:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()
# ================== LOAD USER IBs FROM CSV ==================
if st.session_state.logged_in and not st.session_state.ib_rows:
    user_df = df[df["Employee"] == st.session_state.user]

    for ib in user_df["IB"].dropna().unique():
        latest = user_df[user_df["IB"] == ib].sort_values("Time").iloc[-1]

        st.session_state.ib_rows.append({
            "ib": ib,
            "url": latest["URL"],
            "status": latest["Status"],
            "stage": latest["Stage"],
            "date": latest["Date"]
        })
# ================== HEADER ==================
st.markdown(
    f"""
    <div style="display:flex;justify-content:space-between;align-items:center">
        <h2>📊 Time Tracking Dashboard</h2>
        <div><b>👤 {st.session_state.user}</b></div>
    </div><hr>
    """,
    unsafe_allow_html=True
)

if st.button("🔒 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

# ================== FUNCTIONS ==================
def log_action(ib, url, status, stage, action):
    global df

    now = datetime.now(LOCAL_TZ)

    df = pd.concat([df, pd.DataFrame([{
        "Employee": st.session_state.user,
        "IB": ib,
        "URL": url,
        "Status": status,
        "Stage": stage,
        "Action": action,
        "Time": now,
        "Date": now.date()
    }])], ignore_index=True)

    df.to_csv(DATA_FILE, index=False)

def get_stage_events(ib, stage):
    return df[(df["IB"] == ib) & (df["Stage"] == stage)].sort_values("Time")

def get_total_time_str(ib, stage):
    events = get_stage_events(ib, stage)
    total_seconds = 0
    start = None
    for _, r in events.iterrows():
        if r["Action"] in ["Start", "Resume"]:
            start = r["Time"]
        elif r["Action"] in ["Pause", "Stop"] and start is not None:
            total_seconds += int((r["Time"] - start).total_seconds())
            start = None
    h, m, s = total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

# ================== ADD NEW IB ==================
if st.session_state.user != "admin":
    if st.button("➕ Add New IB"):
        st.session_state.ib_rows.append({"ib": "", "url": "", "status": "In Progress", "stage": STAGES[0], "date": datetime.now().date()})

# ================== IB TABLE (NON-ADMIN ONLY) ==================
if st.session_state.user != "admin":

    # ---------- TABLE HEADER ----------
    cols = st.columns([0.6, 1.3, 2, 2, 2, 2, 2.5, 1.2, 1.2, 1.2, 1.2, 1.2, 0.8])
    headers = [
        "S.No", "Date", "IB Name", "URL", "Status", "Stage", "Actions",
        "Start", "Pause", "Resume", "End", "Total", "Delete"
    ]
    for c, h in zip(cols, headers):
        c.markdown(f"**{h}**")

    # ---------- IB ROWS ----------
    for i, row in enumerate(st.session_state.ib_rows):

        cols = st.columns([0.6, 1.3, 2, 2, 2, 2, 2.5, 1.2, 1.2, 1.2, 1.2, 1.2, 0.8])

        # S.No
        cols[0].markdown(f"**{i + 1}**")

        # Date
        if "date" not in row or not row["date"]:
            row["date"] = datetime.now().date()
        row["date"] = cols[1].date_input(
             "",
            value=row["date"],
            key=f"date_{i}",
            label_visibility="collapsed"
        )

        # IB Name
        row["ib"] = cols[2].text_input(
            "", row.get("ib", ""), key=f"ib_{i}", label_visibility="collapsed"
        )

        # URL
        row["url"] = cols[3].text_input(
            "", row.get("url", ""), key=f"url_{i}", label_visibility="collapsed"
        )

        # Status
        row["status"] = cols[4].selectbox(
            "", STATUS_OPTIONS, index=STATUS_OPTIONS.index(row["status"]),
            key=f"status_{i}", label_visibility="collapsed"
        )

        # Stage
        row["stage"] = cols[5].selectbox(
            "", STAGES, index=STAGES.index(row["stage"]),
            key=f"stage_{i}", label_visibility="collapsed"
        )

        ib_key = row["ib"]
        stage_key = row["stage"]

        # ---------- ACTION BUTTONS ----------
        with cols[6]:
            active_key = f"state_active_{i}"
            pause_key  = f"state_pause_{i}"
            resume_key = f"state_resume_{i}"
            stop_key   = f"state_stop_{i}"


            st.session_state.setdefault(active_key, False)
            st.session_state.setdefault(pause_key, False)
            st.session_state.setdefault(resume_key, False)
            st.session_state.setdefault(stop_key, False)

            start_icon  = "🟢▶" if st.session_state[active_key] else "⚪▶"
            pause_icon  = "🟡⏸" if st.session_state[pause_key] else "⚪⏸"
            resume_icon = "🟡🔄" if st.session_state[resume_key] else "⚪🔄"
            stop_icon   = "🔴⏹" if st.session_state[stop_key] else "⚪⏹"

            b1, b2, b3, b4 = st.columns(4)

            if b1.button(start_icon, key=f"start_{i}"):
                log_action(ib_key, row["url"], row["status"], stage_key, "Start")
                st.session_state[active_key] = True
                st.session_state[pause_key] = False
                st.session_state[resume_key] = False
                st.session_state[stop_key] = False
                st.rerun()

            if b2.button(pause_icon, key=f"pause_{i}"):
                if st.session_state[active_key]:
                    log_action(ib_key, row["url"], row["status"], stage_key, "Pause")
                    st.session_state[pause_key] = True
                    st.rerun()

            if b3.button(resume_icon, key=f"resume_{i}"):
                if st.session_state[pause_key]:
                    log_action(ib_key, row["url"], row["status"], stage_key, "Resume")
                    st.session_state[pause_key] = False
                    st.session_state[resume_key] = True
                    st.session_state[stop_key] = False
                    st.rerun()

            if b4.button(stop_icon, key=f"stop_{i}"):
                if st.session_state[active_key]:
                    log_action(ib_key, row["url"], row["status"], stage_key, "Stop")
                    st.session_state[active_key] = False
                    st.session_state[pause_key] = False
                    st.session_state[resume_key] = False
                    st.session_state[stop_key] = True
                    st.rerun()

        # ---------- TIME COLUMNS ----------
        events = get_stage_events(ib_key, stage_key)

        def last_time(action):
            f = events[events["Action"] == action]
            return f["Time"].max() if not f.empty else None

        cols[7].write(last_time("Start").strftime("%H:%M:%S") if last_time("Start") else "—")
        cols[8].write(last_time("Pause").strftime("%H:%M:%S") if last_time("Pause") else "—")
        cols[9].write(last_time("Resume").strftime("%H:%M:%S") if last_time("Resume") else "—")
        cols[10].write(last_time("Stop").strftime("%H:%M:%S") if last_time("Stop") else "—")
        cols[11].write(get_total_time_str(ib_key, stage_key))

        # ---------- DELETE ----------
        if cols[12].button("❌", key=f"delete_{i}"):
            st.session_state.ib_rows.pop(i)
            st.rerun()

# ================== ADMIN DASHBOARD ==================
if st.session_state.user == "admin":
    st.title("🧑‍💼 Admin Dashboard")
    events = df.copy()

    st.subheader("📌 All Events")
    st.dataframe(events, use_container_width=True)

    # Restart IB (per IB)
    st.subheader("🔄 Restart IB (Admin Only)")
    if not events.empty:
        ib = st.selectbox("Select IB", events["IB"].unique())
        confirm = st.checkbox("Confirm delete")
        if st.button("Restart IB") and confirm:
            df = df[df["IB"] != ib]
            df.to_csv(DATA_FILE, index=False)
            st.success("IB reset successfully")
            st.rerun()

    # Delete All IBs
    st.subheader("🗑 Delete All IBs (Admin Only)")
    confirm_all = st.checkbox("Confirm delete all IBs")
    if st.button("Delete All IBs") and confirm_all:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)
        df.to_csv(DATA_FILE, index=False)
        st.session_state.ib_rows = []
        st.success("All IBs deleted successfully")
        st.rerun()

    # ================== Time summary ==================
    st.subheader("📊 Time Summary")
    summary_data = []

    for i, ib in enumerate(events["IB"].unique()):
        ib_events = events[events["IB"] == ib]
        row_summary = {
          "Sl.no": i + 1,
          "Employee": ib_events["Employee"].iloc[0] if not ib_events.empty else "—",
          "Date": ib_events["Date"].iloc[0] if not ib_events.empty else "—",
          "IB Name": ib
        }

        total_seconds_all_stages = 0

        for stage in STAGES:
            events_stage = get_stage_events(ib, stage)
            stage_seconds = 0
            start = None
            for _, r in events_stage.iterrows():
                if r["Action"] in ["Start", "Resume"]:
                    start = r["Time"]
                elif r["Action"] in ["Pause", "Stop"] and start is not None:
                    stage_seconds += int((r["Time"] - start).total_seconds())
                    start = None
            hours = stage_seconds // 3600
            minutes = (stage_seconds % 3600) // 60
            seconds = stage_seconds % 60
            row_summary[stage] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            total_seconds_all_stages += stage_seconds

        row_summary["Total Time (min)"] = round(total_seconds_all_stages / 60, 2)
        summary_data.append(row_summary)

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)

    # Download Excel
    def to_excel(data):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            data.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        "⬇ Download Excel",
        to_excel(summary_df),
        "IB_Time_Report.xlsx"
    )
