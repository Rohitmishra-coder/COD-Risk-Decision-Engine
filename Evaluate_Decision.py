import pandas as pd

# Load decision log
df = pd.read_csv("decision_log.csv")

# Keep only orders with final outcomes
df["final_status"] = df["final_status"].str.upper().str.strip()

df = df[
    df["final_status"].isin(["DELIVERED", "RTO"])
].copy()

# Create RTO target
df["is_rto"] = (df["final_status"] == "RTO").astype(int)

# Calculate performance by decision
summary = (
    df.groupby("decision")
    .agg(
        orders=("order_id", "count"),
        rtos=("is_rto", "sum"),
        delivered=("is_rto", lambda x: (x == 0).sum()),
        rto_rate=("is_rto", "mean")
    )
    .reset_index()
)

summary["rto_rate"] = (
    summary["rto_rate"] * 100
).round(2)

print("\n===== RTO RATE BY DECISION =====")
print(summary.to_string(index=False))

# Overall baseline
overall_rto = df["is_rto"].mean() * 100

print("\n===== OVERALL RTO RATE =====")
print(round(overall_rto, 2), "%")

# Compare each group with overall baseline
print("\n===== RISK COMPARISON =====")

for _, row in summary.iterrows():
    difference = row["rto_rate"] - overall_rto

    print(
        f"{row['decision']}: "
        f"{difference:+.2f} percentage points "
        "compared with overall RTO rate"
    )