
import pandas as pd

# ==========================================
# 1. LOAD DATA
# ==========================================

df = pd.read_csv("decision_log.csv")

df["order_datetime"] = pd.to_datetime(
    df["order_datetime"],
    errors="coerce"
)

df["final_status"] = (
    df["final_status"]
    .astype(str)
    .str.upper()
    .str.strip()
)

df["order_value"] = pd.to_numeric(
    df["order_value"],
    errors="coerce"
)

# Only use orders with known final outcomes
df = df[
    df["final_status"].isin(["DELIVERED", "RTO"])
].copy()

# Remove records without valid dates
df = df.dropna(subset=["order_datetime"])

# Sort orders chronologically
df = df.sort_values(
    "order_datetime"
).reset_index(drop=True)

# RTO indicator
df["is_rto"] = (
    df["final_status"] == "RTO"
).astype(int)

# ==========================================
# 2. CHRONOLOGICAL 80/20 SPLIT
# ==========================================

split_index = int(len(df) * 0.80)

train_df = df.iloc[:split_index].copy()
test_df = df.iloc[split_index:].copy()

print("\n========== BACKTEST DATA SPLIT ==========")

print("Total evaluated orders:", len(df))
print("Training orders:", len(train_df))
print("Testing orders:", len(test_df))

print(
    "Training period:",
    train_df["order_datetime"].min(),
    "to",
    train_df["order_datetime"].max()
)

print(
    "Testing period:",
    test_df["order_datetime"].min(),
    "to",
    test_df["order_datetime"].max()
)

# ==========================================
# 3. PERFORMANCE FUNCTION
# ==========================================

def evaluate_performance(data, period_name):

    total_orders = len(data)
    total_rtos = int(data["is_rto"].sum())

    delivered = total_orders - total_rtos

    rto_rate = (
        total_rtos / total_orders * 100
        if total_orders > 0 else 0
    )

    print(f"\n========== {period_name} PERFORMANCE ==========")

    print("Total orders:", total_orders)
    print("Delivered orders:", delivered)
    print("RTO orders:", total_rtos)
    print(f"RTO rate: {rto_rate:.2f}%")

    # Performance by initial decision
    decision_summary = (
        data.groupby("decision")
        .agg(
            orders=("order_id", "count"),
            rtos=("is_rto", "sum"),
            delivered=("is_rto", lambda x: (x == 0).sum()),
            rto_rate=("is_rto", "mean")
        )
    )

    decision_summary["rto_rate"] *= 100

    print("\nRTO PERFORMANCE BY DECISION")
    print(
        decision_summary.round(2).to_string()
    )

    return {
        "period": period_name,
        "orders": total_orders,
        "delivered": delivered,
        "rtos": total_rtos,
        "rto_rate": rto_rate
    }

# ==========================================
# 4. EVALUATE BOTH PERIODS
# ==========================================

train_results = evaluate_performance(
    train_df,
    "TRAINING PERIOD (EARLIEST 80%)"
)

test_results = evaluate_performance(
    test_df,
    "TEST PERIOD (LATEST 20%)"
)

# ==========================================
# 5. COMPARE TRAINING AND TEST RESULTS
# ==========================================

comparison = pd.DataFrame([
    train_results,
    test_results
])

print("\n========== TRAINING VS TEST COMPARISON ==========")

print(
    comparison.round(2).to_string(index=False)
)

rto_rate_difference = (
    test_results["rto_rate"]
    - train_results["rto_rate"]
)

print(
    "\nTest minus training RTO rate:",
    f"{rto_rate_difference:+.2f} percentage points"
)

# ==========================================
# 6. SAVE RESULTS
# ==========================================

comparison.to_csv(
    "backtest_summary.csv",
    index=False
)

print("\nBacktest summary saved to backtest_summary.csv")

# ==========================================
# 7. IMPORTANT LIMITATION
# ==========================================

print("""
IMPORTANT:
This is a chronological historical evaluation of the
existing decision rules.

The rules were developed after examining this dataset.
Therefore, the latest 20% is not a fully independent
prospective test set.

Historical RTO differences do not prove that the
decision engine caused an improvement.
""")
