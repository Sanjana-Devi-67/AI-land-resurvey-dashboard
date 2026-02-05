import pandas as pd
import numpy as np

# -----------------------------
# Load Data
# -----------------------------
ror_df = pd.read_csv("data/raw/ror_records.csv")
resurvey_df = pd.read_csv("data/raw/resurvey_data.csv")
boundary_df = pd.read_csv("data/raw/boundary_flags.csv")

# -----------------------------
# Merge Data
# -----------------------------
df = ror_df.merge(resurvey_df, on="parcel_id", how="left")
df = df.merge(boundary_df, on="parcel_id", how="left")

# -----------------------------
# Conflict Detection
# -----------------------------
df["area_diff"] = df["resurvey_area"] - df["ror_area"]
df["area_diff_pct"] = (df["area_diff"] / df["ror_area"]) * 100

def detect_area_conflict(pct):
    if abs(pct) > 25:
        return "Severe Area Mismatch"
    elif abs(pct) > 10:
        return "Moderate Area Mismatch"
    else:
        return "No Area Conflict"

df["area_conflict"] = df["area_diff_pct"].apply(detect_area_conflict)

df["boundary_conflict"] = df["overlap_flag"].apply(
    lambda x: "Boundary Overlap" if x == "Yes" else "No Boundary Conflict"
)

# -----------------------------
# Risk Scoring (AI-assisted)
# -----------------------------
def calculate_risk(row):
    score = 0

    # Area-based risk
    if abs(row["area_diff_pct"]) > 25:
        score += 50
    elif abs(row["area_diff_pct"]) > 10:
        score += 30

    # Boundary overlap risk
    if row["overlap_flag"] == "Yes":
        score += 40

    # Land type sensitivity
    if row["land_type"] == "Commercial":
        score += 20

    return score

df["risk_score"] = df.apply(calculate_risk, axis=1)

def risk_label(score):
    if score >= 70:
        return "High"
    elif score >= 40:
        return "Medium"
    else:
        return "Low"

df["risk_level"] = df["risk_score"].apply(risk_label)

# -----------------------------
# Inspector Status (initial)
# -----------------------------
df["inspection_status"] = "Pending"
df["inspector_remarks"] = ""

# -----------------------------
# Save Outputs
# -----------------------------
df.to_csv("outputs/conflict_analysis_report.csv", index=False)

print("✅ Conflict analysis completed")
print(df[["parcel_id", "area_conflict", "boundary_conflict", "risk_level"]].head())
