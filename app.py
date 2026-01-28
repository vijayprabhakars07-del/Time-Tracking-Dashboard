import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Time Tracking Dashboard", layout="wide")

# ---------------- USERS ----------------
USERS = {
    "admin": "admin123",
    "Revathi": "revathi123",
    "Jayalakshmi": "jaya123",
    "Chithra": "chitra123",
    "Bhavani": "bhavani123",
    "Vijay": "vijay123",

}

PROCESSES = [
    "Analyse",
    "Configuration",
    "Add Section",
    "Extraction",
    "Self-QA",
    "QA",
    "Error Clearing",
    "QA (Error Cleared)"
]

STATUS_OPTIONS = ["Start", "Pause", "Completed"]
DATA_FILE = "data.csv"

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# ---------------- DATA INIT ----------------
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=[
        "Employee", "Source Name", "Source URL",
        "Process", "Status", "Updated Time"
    ]).to_csv(DATA_FILE, index=False)

df = pd.read_csv(DATA_FILE)
if not df.empty:
    df["Updated Time"] = pd.to_datetime(df["Updated Time"])

# ---------------- LOGIN ----------------
if not st.session_state.logged_in:

    st.markdown("""
        <h1 style="text-align:center; margin-bottom:10px;">
            ⏱️ Time Tracking Dashboard
        </h1>
        <p style="text-align:center; font-size:16px; color:gray; margin-bottom:40px;">
            Secure employee time & process monitoring
        </p>
    """, unsafe_allow_html=True)
    
if not st.session_state.logged_in:
    st.title("🔐 Login")

    username = st.selectbox("Username", list(USERS.keys()))
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if USERS.get(username) == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ---------------- LOGOUT ----------------
st.sidebar.write(f"👤 Logged in as: {st.session_state.user}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

user = st.session_state.user

# ======================================================
# EMPLOYEE VIEW
# ======================================================
if user != "admin":

    st.sidebar.title("🧑‍💻 Update Work Status")

    source_name = st.sidebar.text_input("Source Name")
    source_url = st.sidebar.text_input("Source URL")
    process = st.sidebar.selectbox("Process Stage", PROCESSES)
    status = st.sidebar.selectbox("Status", STATUS_OPTIONS)

    if st.sidebar.button("Save / Update"):
        if source_name.strip():
            new_row = {
                "Employee": user,
                "Source Name": source_name,
                "Source URL": source_url,
                "Process": process,
                "Status": status,
                "Updated Time": datetime.now()
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.sidebar.success("Updated successfully")
        else:
            st.sidebar.error("Source Name required")

    st.title("📊 Time Tracking Dashboard")
    st.dataframe(df[df["Employee"] == user], use_container_width=True)

# ======================================================
# ADMIN VIEW
# ======================================================
else:
    st.title("🧑‍💼 Admin Dashboard")

    # ---------- RAW DATA ----------
    st.subheader("📌 All Activity Records")
    st.dataframe(df, use_container_width=True)

    # ---------- RESTART SOURCE ----------
    st.subheader("🔄 Restart Source")

    if not df.empty:
        source = st.selectbox("Select Source", df["Source Name"].unique())
        confirm = st.checkbox("Confirm restart (this will delete all data for the source)")

        if st.button("Restart Source"):
            if confirm:
                df = df[df["Source Name"] != source]
                df.to_csv(DATA_FILE, index=False)
                st.success(f"Source '{source}' restarted successfully")
                st.rerun()
            else:
                st.warning("Please confirm before restarting")


# ======================================================
# TIME CALCULATION LOGIC
# ======================================================
def calculate_time_taken(data):
    results = []

    for (emp, src, proc), group in data.groupby(
        ["Employee", "Source Name", "Process"]
    ):
        group = group.sort_values("Updated Time")

        total_minutes = 0
        start_time = None

        for _, row in group.iterrows():
            if row["Status"] == "Start":
                start_time = row["Updated Time"]

            elif row["Status"] in ["Pause", "Completed"] and start_time is not None:
                diff = (row["Updated Time"] - start_time).total_seconds() / 60
                total_minutes += diff
                start_time = None

        results.append({
            "Employee": emp,
            "Source Name": src,
            "Process": proc,
            "Start Time": group[group["Status"] == "Start"]["Updated Time"].min(),
            "Completed Time": group[group["Status"] == "Completed"]["Updated Time"].max(),
            "Total Time Taken (Minutes)": round(total_minutes, 2)
        })

    return pd.DataFrame(results)

# ======================================================
# TIME SUMMARY EXCEL (ADMIN ONLY)
# ======================================================
if user == "admin":
    st.subheader("⏱ Time Taken Summary (Minutes)")

    summary_df = calculate_time_taken(df)
    st.dataframe(summary_df, use_container_width=True)

    def to_excel_summary(data):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            data.to_excel(writer, index=False, sheet_name="Time Summary")
        return output.getvalue()

    st.download_button(
        "📥 Download Time Summary Excel",
        to_excel_summary(summary_df),
        "time_tracking_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )