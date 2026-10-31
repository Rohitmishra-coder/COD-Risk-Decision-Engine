
import pandas as pd
import json
import re

# ==========================================
# 1. LOAD FROZEN CONFIGURATION
# ==========================================

with open("config.json", "r") as file:
    config = json.load(file)

print("Configuration loaded:")
print(json.dumps(config, indent=4))


# ==========================================
# 2. LOAD AND CLEAN DATA
# ==========================================

df = pd.read_csv(
    "orders_sample.csv",
    dtype={
        "phone": "string",
        "pincode": "string"
    }
)

original_count = len(df)

df = df.drop_duplicates().copy()

print("\n========== DATA CLEANING ==========")
print("Original records:", original_count)
print("Duplicate records removed:", original_count - len(df))
print("Records after cleaning:", len(df))

df["final_status"] = (
    df["final_status"].astype(str).str.upper().str.strip()
)

df["utm_source"] = (
    df["utm_source"].astype(str).str.lower().str.strip()
)

df["customer_prior_orders"] = pd.to_numeric(
    df["customer_prior_orders"], errors="coerce"
)

df["customer_prior_rto"] = pd.to_numeric(
    df["customer_prior_rto"], errors="coerce"
)

df["order_datetime"] = pd.to_datetime(
    df["order_datetime"], errors="coerce"
)

df["order_value"] = pd.to_numeric(
    df["order_value"], errors="coerce"
)

# Keep only orders with known outcomes and valid dates.
df = df[
    df["final_status"].isin(["DELIVERED", "RTO"])
].dropna(subset=["order_datetime"]).copy()

df = df.sort_values(
    "order_datetime"
).reset_index(drop=True)

df["is_rto"] = (
    df["final_status"] == "RTO"
).astype(int)


# ==========================================
# 3. CHRONOLOGICAL 80/20 SPLIT
# ==========================================

split_index = int(len(df) * 0.80)

print("\n========== DATA SPLIT ==========")

print("Total evaluated orders:", len(df))
print("Training orders:", split_index)
print("Testing orders:", len(df) - split_index)

print(
    "\nTraining period:",
    df.iloc[:split_index]["order_datetime"].min(),
    "to",
    df.iloc[:split_index]["order_datetime"].max()
)

print(
    "Testing period:",
    df.iloc[split_index:]["order_datetime"].min(),
    "to",
    df.iloc[split_index:]["order_datetime"].max()
)


# ==========================================
# 4. RECREATE DECISION ENGINE FEATURES
# ==========================================

def identify_customer_type(value):

    if pd.isna(value):
        return "Unknown"

    if value == 0:
        return "First-time"

    return "Returning"


def valid_phone(phone):

    if pd.isna(phone):
        return False

    digits = re.sub(r"\D", "", str(phone))

    return len(digits) == 10


def valid_pincode(pincode):

    if pd.isna(pincode):
        return False

    return bool(
        re.fullmatch(r"\d{6}", str(pincode).strip())
    )


df["customer_type"] = (
    df["customer_prior_orders"]
    .apply(identify_customer_type)
)

df["valid_phone"] = (
    df["phone"].apply(valid_phone)
)

df["valid_pincode"] = (
    df["pincode"].apply(valid_pincode)
)


# ==========================================
# 5. APPLY FROZEN FOUR-CATEGORY RULES
# ==========================================

def make_decision(row):

    # RULE 1: Inconsistent customer history
    # Hold for manual review.

    if (
        pd.notna(row["customer_prior_orders"])
        and pd.notna(row["customer_prior_rto"])
        and row["customer_prior_rto"] > row["customer_prior_orders"]
    ):

        return (
            "hold/cancel",
            "Customer history contains inconsistent RTO records"
        )

    # RULE 2: Missing customer history

    if (
        pd.isna(row["customer_prior_orders"])
        or pd.isna(row["customer_prior_rto"])
    ):

        return (
            "ship after WhatsApp confirmation",
            "Customer history needs verification"
        )

    # RULE 3: Phone validation

    if (
        config["require_valid_phone"]
        and not row["valid_phone"]
    ):

        return (
            "ship after WhatsApp confirmation",
            "Phone number needs verification"
        )

    # RULE 4: Pincode validation

    if (
        config["require_valid_pincode"]
        and not row["valid_pincode"]
    ):

        return (
            "ship after WhatsApp confirmation",
            "Pincode needs verification"
        )

    # RULE 5: City validation

    if (
        pd.isna(row["city"])
        or str(row["city"]).strip() == ""
    ):

        return (
            "ship after WhatsApp confirmation",
            "City information is missing"
        )

    # RULE 6: Previous RTO history

    if (
        row["customer_prior_rto"]
        >= config["prior_rto_confirmation_threshold"]
    ):

        return (
            "ship after WhatsApp confirmation",
            "Customer has previous RTO history"
        )

    # RULE 7: Marketing source and customer type

    if (
        row["utm_source"] in config["high_risk_sources"]
        and row["customer_type"] in config["high_risk_customer_types"]
    ):

        return (
            "nudge to prepaid",
            "First-time customer from a higher-RTO marketing cohort"
        )

    # RULE 8: Default decision

    return (
        "ship as-is",
        "No additional risk condition identified"
    )


# Recalculate decisions without using final_status.

results = df.apply(make_decision, axis=1)

df["predicted_decision"] = results.apply(
    lambda x: x[0]
)

df["predicted_reason"] = results.apply(
    lambda x: x[1]
)


# ==========================================
# 6. RECREATE TRAINING AND TESTING DATASETS
# ==========================================

train_df = df.iloc[:split_index].copy()

test_df = df.iloc[split_index:].copy()


# ==========================================
# 7. VERIFY DECISION REPRODUCTION
# ==========================================

original_results = pd.read_csv(
    "decision_log.csv",
    dtype={
        "phone": "string",
        "pincode": "string"
    }
)

original_results = original_results.drop_duplicates().copy()

comparison = df[
    ["order_id", "predicted_decision"]
].merge(
    original_results[
        ["order_id", "decision"]
    ],
    on="order_id",
    how="left",
    validate="one_to_one"
)

comparison["decision_matches"] = (
    comparison["predicted_decision"]
    == comparison["decision"]
)

matching = int(comparison["decision_matches"].sum())

different = int(
    (~comparison["decision_matches"]).sum()
)

print("\n========== DECISION REPRODUCTION CHECK ==========")

print("Matching decisions:", matching)
print("Different or missing decisions:", different)
print("Total compared orders:", len(comparison))

if different > 0:

    print("\nMISMATCHED DECISIONS:")

    print(
        comparison.loc[
            ~comparison["decision_matches"]
        ].to_string(index=False)
    )

else:

    print("\nSUCCESS: All decisions match the decision engine.")


# ==========================================
# 8. PERFORMANCE EVALUATION FUNCTION
# ==========================================

def evaluate_performance(data, period_name):

    total_orders = len(data)

    total_rtos = int(data["is_rto"].sum())

    delivered = total_orders - total_rtos

    rto_rate = (
        total_rtos / total_orders * 100
        if total_orders > 0 else 0
    )

    print(f"\n========== {period_name} ==========")

    print("Orders:", total_orders)
    print("Delivered:", delivered)
    print("RTOs:", total_rtos)
    print(f"Overall RTO rate: {rto_rate:.2f}%")

    summary = (
        data.groupby("predicted_decision")
        .agg(
            orders=("order_id", "count"),
            rtos=("is_rto", "sum"),
            delivered=("is_rto", lambda x: (x == 0).sum()),
            rto_rate=("is_rto", "mean")
        )
    )

    summary["rto_rate"] *= 100

    print("\nRTO PERFORMANCE BY PREDICTED DECISION")

    print(
        summary.round(2).to_string()
    )

    return summary


# ==========================================
# 9. EVALUATE TRAINING AND TEST PERIODS
# ==========================================

train_summary = evaluate_performance(
    train_df,
    "TRAINING PERIOD - EARLIEST 80%"
)

test_summary = evaluate_performance(
    test_df,
    "TEST PERIOD - LATEST 20%"
)


# ==========================================
# 10. COMPARE OVERALL PERFORMANCE
# ==========================================

train_rto_rate = (
    train_df["is_rto"].mean() * 100
)

test_rto_rate = (
    test_df["is_rto"].mean() * 100
)

print("\n========== OVERALL COMPARISON ==========")

print(f"Training RTO rate: {train_rto_rate:.2f}%")
print(f"Testing RTO rate: {test_rto_rate:.2f}%")

print(
    "Test minus training:",
    f"{test_rto_rate - train_rto_rate:+.2f} percentage points"
)


# ==========================================
# 11. SAVE TEST PREDICTIONS
# ==========================================

test_predictions = test_df[
    [
        "order_id",
        "order_datetime",
        "order_value",
        "final_status",
        "is_rto",
        "predicted_decision",
        "predicted_reason"
    ]
].copy()

test_predictions.to_csv(
    "backtest_v2_test_predictions.csv",
    index=False
)


# ==========================================
# 12. TEST PERIOD FINANCIAL EVALUATION
# ==========================================

RTO_COST = 169.40

GROSS_MARGIN_RATE = 0.62

print("\n========== TEST PERIOD FINANCIAL EVALUATION ==========")

# Exclude missing and non-positive order values.

valid_value_data = test_predictions[
    test_predictions["order_value"].notna()
    & (test_predictions["order_value"] > 0)
].copy()


financial_summary = valid_value_data.groupby(
    "predicted_decision"
).agg(
    orders=("order_id", "count"),
    rtos=("is_rto", "sum"),
    total_order_value=("order_value", "sum")
)

financial_summary["delivered"] = (
    financial_summary["orders"]
    - financial_summary["rtos"]
)

financial_summary["rto_rate_percent"] = (
    financial_summary["rtos"]
    / financial_summary["orders"] * 100
)

# Historical RTO cost.

financial_summary["historical_rto_cost"] = (
    financial_summary["rtos"] * RTO_COST
)

# Delivered gross margin.

delivered_margin = (
    valid_value_data[
        valid_value_data["final_status"] == "DELIVERED"
    ]
    .groupby("predicted_decision")["order_value"]
    .sum()
    * GROSS_MARGIN_RATE
)

financial_summary["delivered_gross_margin"] = (
    delivered_margin
    .reindex(financial_summary.index)
    .fillna(0)
)

print("\nFINANCIAL BREAKDOWN BY DECISION")

print(
    financial_summary.round(2).to_string()
)


# Overall test-period financial totals.

total_test_rto_cost = (
    valid_value_data["is_rto"].sum() * RTO_COST
)

total_delivered_margin = (
    valid_value_data.loc[
        valid_value_data["final_status"] == "DELIVERED",
        "order_value"
    ].sum() * GROSS_MARGIN_RATE
)

print("\nOVERALL TEST PERIOD FINANCIAL TOTALS")

print(
    f"Historical RTO cost: Rs. {total_test_rto_cost:,.2f}"
)

print(
    f"Delivered gross margin: Rs. {total_delivered_margin:,.2f}"
)

print(
    "\nOrders excluded due to missing or non-positive value:",
    len(test_predictions) - len(valid_value_data)
)

financial_summary.to_csv(
    "backtest_v2_test_financial_summary.csv"
)

print(
    "\nSaved: backtest_v2_test_financial_summary.csv"
)


# ==========================================
# 13. SAVE ALL BACKTEST RESULTS
# ==========================================

train_summary.to_csv(
    "backtest_v2_training.csv"
)

test_summary.to_csv(
    "backtest_v2_testing.csv"
)

comparison.to_csv(
    "backtest_v2_decision_check.csv",
    index=False
)

print("\n========== FILES SAVED ==========")

print("backtest_v2_training.csv")
print("backtest_v2_testing.csv")
print("backtest_v2_decision_check.csv")
print("backtest_v2_test_predictions.csv")
print("backtest_v2_test_financial_summary.csv")


# ==========================================
# 14. LIMITATIONS
# ==========================================

print("""
IMPORTANT LIMITATIONS:

1. The decision rules and configuration are frozen.
2. final_status is not used to make decisions.
3. final_status is used only for retrospective evaluation.
4. The rules were originally developed after examining
   the full dataset, so this is not an independent test.
5. RTO differences do not prove that the decision engine
   caused an improvement.
6. Historical RTO costs are not actual savings generated
   by the decision engine.
7. Delivered gross margin is historical margin, not
   incremental profit caused by the engine.
8. Financial calculations exclude orders with missing
   or non-positive order values.
9. hold/cancel means manual review in this implementation,
   not automatic cancellation.
""")
