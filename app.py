import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# =========================================================
# Page Config
# =========================================================
st.set_page_config(
    page_title="AI Land Resurvey Dashboard",
    layout="wide"
)

# =========================================================
# Load Data
# =========================================================
@st.cache_data
def load_data():
    return pd.read_csv("outputs/conflict_analysis_report.csv")

df = load_data()

# =========================================================
# Sidebar Navigation
# =========================================================
st.sidebar.title("🧭 Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "🏠 Overview",
        "📥 Export Reports",
        "🎚️ Policy Thresholds",
        "🧭 Zone Aggregation",
        "⏱️ Inspection SLA"
    ]
)

# =========================================================
# 🏠 OVERVIEW PAGE (YOUR EXISTING DASHBOARD)
# =========================================================
if page == "🏠 Overview":

    st.title("🗺️ AI-Assisted Land Resurvey Intelligence Dashboard")
    st.caption("Department of Lands & Revenue | Government of Andhra Pradesh")

    # -----------------------------
    # Global Filters
    # -----------------------------
    st.subheader("🔎 Global Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mandal = st.selectbox("Mandal", ["All"] + sorted(df["mandal"].unique()))

    with col2:
        land_type = st.multiselect(
            "Land Type",
            df["land_type"].unique(),
            default=df["land_type"].unique()
        )

    with col3:
        risk_filter = st.multiselect(
            "Risk Level",
            df["risk_level"].unique(),
            default=df["risk_level"].unique()
        )

    with col4:
        threshold = st.slider("Area Mismatch Threshold (%)", 5, 30, 10)

    filtered_df = df.copy()

    if mandal != "All":
        filtered_df = filtered_df[filtered_df["mandal"] == mandal]

    filtered_df = filtered_df[
        (filtered_df["land_type"].isin(land_type)) &
        (filtered_df["risk_level"].isin(risk_filter)) &
        (abs(filtered_df["area_diff_pct"]) >= threshold)
    ]

    st.divider()

    # -----------------------------
    # KPI Section
    # -----------------------------
    st.subheader("📊 Key Intelligence Indicators")

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric("Total Parcels", len(filtered_df))
    k2.metric("Conflict Parcels", (filtered_df["area_conflict"] != "No Area Conflict").sum())
    k3.metric("High Risk Parcels", (filtered_df["risk_level"] == "High").sum())
    k4.metric("Verified Parcels", (filtered_df["inspection_status"] == "Verified").sum())
    k5.metric("Pending Inspections", (filtered_df["inspection_status"] == "Pending").sum())

    st.divider()

    # -----------------------------
    # Geospatial Risk Map
    # -----------------------------
    st.subheader("🗺️ Geospatial Risk Visualization")

    center_lat = filtered_df["latitude"].mean()
    center_lon = filtered_df["longitude"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles="CartoDB positron"
    )

    def risk_color(level):
        return {"High": "red", "Medium": "orange", "Low": "green"}[level]

    for _, row in filtered_df.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=6,
            color=risk_color(row["risk_level"]),
            fill=True,
            fill_opacity=0.8,
            popup=f"""
            <b>Parcel:</b> {row['parcel_id']}<br>
            <b>Owner:</b> {row['owner_name']}<br>
            <b>Area Diff:</b> {row['area_diff_pct']:.2f}%<br>
            <b>Risk:</b> {row['risk_level']}
            """
        ).add_to(m)

    st_folium(m, width=1200, height=450)
    st.divider()

    # -----------------------------
    # Conflict Analytics
    # -----------------------------
    st.subheader("📊 Conflict Analytics")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.bar_chart(filtered_df["area_conflict"].value_counts())

    with c2:
        st.bar_chart(filtered_df["risk_level"].value_counts())

    with c3:
        land_risk = filtered_df.groupby(
            ["land_type", "risk_level"]
        ).size().unstack(fill_value=0)
        st.bar_chart(land_risk)

    st.divider()

    # -----------------------------
    # Priority Inspection List
    # -----------------------------
    st.subheader("🚨 Priority Inspection List")

    priority_df = filtered_df.sort_values("risk_score", ascending=False)

    st.dataframe(
        priority_df[
            ["parcel_id", "land_type", "area_diff_pct", "risk_score", "risk_level"]
        ],
        use_container_width=True
    )

    st.divider()

    # -----------------------------
    # Inspector Validation
    # -----------------------------
    st.subheader("🧾 Inspector Validation")

    parcel_ids = filtered_df["parcel_id"].tolist()

    if parcel_ids:
        selected = st.selectbox("Select Parcel", parcel_ids)
        row = df[df["parcel_id"] == selected].iloc[0]

        status = st.selectbox(
            "Inspection Status",
            ["Pending", "Verified", "Dispute"],
            index=["Pending", "Verified", "Dispute"].index(row["inspection_status"])
        )

        remarks = st.text_area("Remarks", row["inspector_remarks"])

        if st.button("Save Update"):
            df.loc[df["parcel_id"] == selected, "inspection_status"] = status
            df.loc[df["parcel_id"] == selected, "inspector_remarks"] = remarks
            df.to_csv("outputs/conflict_analysis_report.csv", index=False)

            # Clear cache and reload fresh data
            st.cache_data.clear()
            df = load_data()

            st.success("Inspection status updated and saved successfully.")


    st.divider()

    # -----------------------------
    # Summary
    # -----------------------------
    st.subheader("🧠 AI-Generated Summary")

    st.info(
        f"""
        • High-risk parcels: {(filtered_df['risk_level'] == 'High').sum()}  
        • Boundary conflicts: {(filtered_df['boundary_conflict'] == 'Boundary Overlap').sum()}  
        • Pending inspections: {(filtered_df['inspection_status'] == 'Pending').sum()}  

        **Recommendation:** Prioritize high-risk and boundary conflict parcels.
        """
    )

# =========================================================
# 📥 EXPORT REPORTS
# =========================================================
elif page == "📥 Export Reports":
    st.title("📥 Export Reports")
    st.download_button(
        "Download Full Conflict Report",
        df.to_csv(index=False),
        file_name="land_resurvey_report.csv"
    )

# =========================================================
# 🎚️ POLICY THRESHOLDS
# =========================================================
elif page == "🎚️ Policy Thresholds":
    st.title("🎚️ Policy Threshold Simulation")

    policy = st.selectbox("Policy Mode", ["Strict", "Balanced", "Conservative"])
    threshold = {"Strict": 5, "Balanced": 10, "Conservative": 20}[policy]

    st.info(f"Area mismatch threshold = {threshold}%")

    df["policy_flag"] = np.where(
        abs(df["area_diff_pct"]) >= threshold,
        "Flagged",
        "Acceptable"
    )

    st.dataframe(df[["parcel_id", "area_diff_pct", "policy_flag"]])

# =========================================================
# 🧭 ZONE AGGREGATION
# =========================================================
elif page == "🧭 Zone Aggregation":
    st.title("🧭 Zone-wise Risk Aggregation")

    median_lat = df["latitude"].median()
    df["zone"] = np.where(df["latitude"] >= median_lat, "North Zone", "South Zone")

    zone_summary = df.groupby(["zone", "risk_level"]).size().unstack(fill_value=0)
    st.bar_chart(zone_summary)
    st.dataframe(zone_summary)

# =========================================================
# ⏱️ INSPECTION SLA
# =========================================================
elif page == "⏱️ Inspection SLA":
    st.title("⏱️ Inspection SLA Monitoring")

    df["inspection_start"] = datetime.now() - pd.to_timedelta(
        np.random.randint(1, 15, len(df)), unit="D"
    )

    df["days_elapsed"] = (datetime.now() - df["inspection_start"]).dt.days
    df["sla_status"] = np.where(df["days_elapsed"] > 7, "Breached", "Within SLA")

    st.dataframe(df[["parcel_id", "days_elapsed", "sla_status"]])
    st.bar_chart(df["sla_status"].value_counts())
