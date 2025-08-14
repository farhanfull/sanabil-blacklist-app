# app.py — Streamlit UI (uses db.py)

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

import db  # our helper module

TZ = pytz.timezone("Africa/Mogadishu")

st.set_page_config(page_title="Sanabil Blacklist Tracker", layout="wide")

# Ensure DB tables exist
db.init_db()

# Sidebar navigation
page = st.sidebar.radio("Navigate", ["Dashboard", "Customers", "Appointments", "Calls", "Import"])

# ---------- Dashboard ----------
if page == "Dashboard":
    st.title("Sanabil Blacklist — Dashboard")

    k = db.kpis()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Customers", k["total_customers"])
    c2.metric("Appointments", k["total_appointments"])
    c3.metric("Calls", k["total_calls"])
    c4.metric("Scheduled", k["scheduled"])
    c5.metric("Upcoming (7d)", k["upcoming7"])

    st.subheader("Upcoming Appointments (next 7 days)")
    appts = db.get_appointments(upcoming_days=7)
    df = pd.DataFrame(appts)
    if not df.empty:
        # Convert UTC strings to Mogadishu local display
        def to_local(s):
            try:
                dt = datetime.fromisoformat(s)
                return pytz.utc.localize(dt).astimezone(TZ).strftime("%Y-%m-%d %H:%M")
            except:
                return s
        df["When (Mogadishu)"] = df["appointment_dt"].apply(to_local)
        st.dataframe(df[["id","customer_name","phone","When (Mogadishu)","status","purpose","location_or_phone","notes"]], use_container_width=True)
    else:
        st.info("No upcoming appointments.")

# ---------- Customers ----------
if page == "Customers":
    st.title("Customers")
    search = st.text_input("Search (name/phone/reason)")
    customers = db.get_customers(search=search)
    st.dataframe(pd.DataFrame(customers), use_container_width=True, height=380)

    st.subheader("Add Customer")
    with st.form("add_customer"):
        name = st.text_input("Full name")
        phone = st.text_input("Phone")
        reason = st.text_input("Reason (Category)")
        submitted = st.form_submit_button("Save")
        if submitted:
            if not name.strip():
                st.error("Name is required.")
            else:
                db.add_customer(name.strip(), phone.strip(), reason.strip())
                st.success("Customer added. Refresh the page to see it in the table.")

# ---------- Appointments ----------
if page == "Appointments":
    st.title("Appointments")
    customers = db.get_customers()
    cust_map = {f"{c['name']} — {c['phone']} (ID {c['id']})": c["id"] for c in customers}
    st.subheader("Schedule / Update Appointment")
    with st.form("add_appt"):
        cust_label = st.selectbox("Customer", list(cust_map.keys()) or ["No customers yet"])
        when = st.datetime_input("Appointment Date/Time (Mogadishu)")
        status = st.selectbox("Status", ["Scheduled","Completed","No-Show","Cancelled","Rescheduled"], index=0)
        purpose = st.text_input("Purpose")
        location_or_phone = st.text_input("Location/Phone")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Appointment")
        if submitted and cust_map:
            # Store as UTC ISO string
            dt_utc = TZ.localize(when).astimezone(pytz.utc).replace(tzinfo=None)
            db.add_appointment(
                customer_id=cust_map[cust_label],
                dt_iso=dt_utc.isoformat(timespec="minutes"),
                status=status,
                purpose=purpose,
                location_or_phone=location_or_phone,
                notes=notes
            )
            st.success("Appointment saved.")

    st.subheader("All Appointments")
    appts = db.get_appointments()
    df = pd.DataFrame(appts)
    if not df.empty:
        def to_local(s):
            try:
                dt = datetime.fromisoformat(s)
                return pytz.utc.localize(dt).astimezone(TZ).strftime("%Y-%m-%d %H:%M")
            except:
                return s
        df["When (Mogadishu)"] = df["appointment_dt"].apply(to_local)
        st.dataframe(df[["id","customer_name","phone","When (Mogadishu)","status","purpose","location_or_phone","notes"]], use_container_width=True)
    else:
        st.info("No appointments yet.")

# ---------- Calls ----------
if page == "Calls":
    st.title("Calls")
    customers = db.get_customers()
    cust_map = {f"{c['name']} — {c['phone']} (ID {c['id']})": c["id"] for c in customers}

    st.subheader("Log a Call")
    with st.form("add_call"):
        cust_label = st.selectbox("Customer", list(cust_map.keys()) or ["No customers yet"])
        when = st.datetime_input("Call Date/Time (Mogadishu)")
        outcome = st.selectbox("Outcome", ["Reached","No Answer","Busy","Switched Off","Invalid Number","Voicemail"], index=0)
        disposition = st.selectbox("Disposition", ["Scheduled","Promise To Pay","Refused","Dispute","Wrong Dept","Follow-up Needed"], index=0)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Call")
        if submitted and cust_map:
            dt_utc = TZ.localize(when).astimezone(pytz.utc).replace(tzinfo=None)
            db.add_call(
                customer_id=cust_map[cust_label],
                dt_iso=dt_utc.isoformat(timespec="minutes"),
                outcome=outcome,
                disposition=disposition,
                notes=notes
            )
            st.success("Call saved.")

    st.subheader("Recent Calls")
    calls = db.get_calls()
    df = pd.DataFrame(calls)
    if not df.empty:
        def to_local(s):
            try:
                dt = datetime.fromisoformat(s)
                return pytz.utc.localize(dt).astimezone(TZ).strftime("%Y-%m-%d %H:%M")
            except:
                return s
        df["When (Mogadishu)"] = df["call_dt"].apply(to_local)
        st.dataframe(df[["id","customer_name","phone","When (Mogadishu)","outcome","disposition","notes"]], use_container_width=True)
    else:
        st.info("No calls yet.")

# ---------- Import ----------
if page == "Import":
    st.title("Import from Excel")
    st.write("Upload your blacklist Excel (minimum columns: **Customer Name**, **Mobile Number**/**Phone**, **Category**).")
    file = st.file_uploader("Upload .xlsx", type=["xlsx"])
    if file is not None:
        try:
            data = pd.read_excel(file)
            st.write("Preview:")
            st.dataframe(data.head(20), use_container_width=True)

            if st.button("Import customers"):
                name_cols = [c for c in data.columns if str(c).strip().lower() in ["customer name","name"]]
                phone_cols = [c for c in data.columns if "mobile" in str(c).lower() or "phone" in str(c).lower()]
                reason_cols = [c for c in data.columns if "category" in str(c).lower() or "reason" in str(c).lower()]

                name_col = name_cols[0] if name_cols else None
                phone_col = phone_cols[0] if phone_cols else None
                reason_col = reason_cols[0] if reason_cols else None

                added = 0
                for _, r in data.iterrows():
                    name = str(r.get(name_col, "")).strip() if name_col else ""
                    phone = str(r.get(phone_col, "")).strip() if phone_col else ""
                    reason = str(r.get(reason_col, "")).strip() if reason_col else ""
                    if name:
                        db.add_customer(name, phone, reason)
                        added += 1
                st.success(f"Imported {added} customers.")
        except Exception as e:
            st.error(f"Import failed: {e}")
