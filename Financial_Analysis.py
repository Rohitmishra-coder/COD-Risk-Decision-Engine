import pandas as pd

# Assignment economics
AOV = 649
GROSS_MARGIN = 0.62
RTO_COST = 169.40

# Load decision log
df = pd.read_csv("decision_log.csv")

# Keep only final outcomes
df["final_status"] = df["final_status"].str.upper().str.strip()

df = df[
    df["final_status"].isin(["DELIVERED", "RTO"])
].copy()

# Count outcomes
summary = (
    df.groupby("decision")
    .agg(
        orders=("order_id", "count"),
        rtos=("final_status", lambda x: (x == "RTO").sum()),
        delivered=("final_status", lambda x: (x == "DELIVERED").sum())
    )
    .reset_index()
)

# Calculate financial exposure
summary["historical_rto_cost"] = (
    summary["rtos"] * RTO_COST
)

summary["delivered_gross_margin"] = (
    summary["delivered"] * AOV * GROSS_MARGIN
)

summary["rto_rate"] = (
    summary["rtos"] / summary["orders"] * 100
).round(2)

print("\n===== FINANCIAL ANALYSIS =====")

print(
    summary.to_string(
        index=False,
        formatters={
            "historical_rto_cost": "₹{:,.2f}".format,
            "delivered_gross_margin": "₹{:,.2f}".format
        }
    )
)

print("\n===== TOTALS =====")

print("Historical RTO cost:",
      f"₹{summary['historical_rto_cost'].sum():,.2f}")

print("Delivered gross margin:",
      f"₹{summary['delivered_gross_margin'].sum():,.2f}")