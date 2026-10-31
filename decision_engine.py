
import pandas as pd
import json
import re

# ==========================================
# 1. LOAD CONFIGURATION
# ==========================================

with open("config.json", "r") as file:
    config = json.load(file)

print("Configuration loaded:")
print(json.dumps(config, indent=4))


# ==========================================
# 2. LOAD DATASET
# ==========================================

df = pd.read_csv(
    "orders_sample.csv",
    dtype={
        "phone": "string",
        "pincode": "string"
    }
)

# Remove exact duplicate records
original_count = len(df)

df = df.drop_duplicates().copy()

duplicates_removed = original_count - len(df)

print("\n========== DATA CLEANING ==========")
print("Original records:", original_count)
print("Duplicate records removed:", duplicates_removed)
print("Records after cleaning:", len(df))


# ==========================================
# 3. DATA PREPARATION
# ==========================================

df["final_status"] = (
    df["final_status"]
    .astype(str)
    .str.upper()
    .str.strip()
)

df["utm_source"] = (
    df["utm_source"]
    .astype(str)
    .str.lower()
    .str.strip()
)

df["customer_prior_orders"] = pd.to_numeric(
    df["customer_prior_orders"],
    errors="coerce"
)

df["customer_prior_rto"] = pd.to_numeric(
    df["customer_prior_rto"],
    errors="coerce"
)


# ==========================================
# 4. IDENTIFY CUSTOMER TYPE
# ==========================================

def identify_customer_type(value):

    if pd.isna(value):
        return "Unknown"

    if value == 0:
        return "First-time"

    return "Returning"


df["customer_type"] = (
    df["customer_prior_orders"]
    .apply(identify_customer_type)
)


# ==========================================
# 5. VALIDATE PHONE NUMBER
# ==========================================

def valid_phone(phone):

    if pd.isna(phone):
        return False

    digits = re.sub(r"\D", "", str(phone))

    return len(digits) == 10


df["valid_phone"] = (
    df["phone"].apply(valid_phone)
)


# ==========================================
# 6. VALIDATE PINCODE
# ==========================================

def valid_pincode(pincode):

    if pd.isna(pincode):
        return False

    return bool(
        re.fullmatch(r"\d{6}", str(pincode).strip())
    )


df["valid_pincode"] = (
    df["pincode"].apply(valid_pincode)
)


# ==========================================
# 7. INITIAL DECISION ENGINE
# ==========================================

def make_decision(row):

    # --------------------------------------
    # RULE 1: Serious history inconsistency
    # --------------------------------------

    if (
        pd.notna(row["customer_prior_orders"])
        and pd.notna(row["customer_prior_rto"])
        and row["customer_prior_rto"] > row["customer_prior_orders"]
    ):

        return (
            "hold/cancel",
            "Customer history contains inconsistent RTO records"
        )

    # --------------------------------------
    # RULE 2: Missing customer history
    # --------------------------------------

    if (
        pd.isna(row["customer_prior_orders"])
        or pd.isna(row["customer_prior_rto"])
    ):

        return (
            "ship after WhatsApp confirmation",
            "Customer history needs verification"
        )

    # --------------------------------------
    # RULE 3: Phone validation
    # --------------------------------------

    if (
        config["require_valid_phone"]
        and not row["valid_phone"]
    ):

        return (
            "ship after WhatsApp confirmation",
            "Phone number needs verification"
        )

    # --------------------------------------
    # RULE 4: Pincode validation
    # --------------------------------------

    if (
        config["require_valid_pincode"]
        and not row["valid_pincode"]
    ):

        return (
            "ship after WhatsApp confirmation",
            "Pincode needs verification"
        )

    # --------------------------------------
    # RULE 5: City validation
    # --------------------------------------

    if (
        pd.isna(row["city"])
        or str(row["city"]).strip() == ""
    ):

        return (
            "ship after WhatsApp confirmation",
            "City information is missing"
        )

    # --------------------------------------
    # RULE 6: Previous RTO history
    # --------------------------------------

    if (
        row["customer_prior_rto"]
        >= config["prior_rto_confirmation_threshold"]
    ):

        return (
            "ship after WhatsApp confirmation",
            "Customer has previous RTO history"
        )

    # --------------------------------------
    # RULE 7: Marketing source and customer type
    # --------------------------------------

    if (
        row["utm_source"] in config["high_risk_sources"]
        and row["customer_type"] in config["high_risk_customer_types"]
    ):

        return (
            "nudge to prepaid",
            "First-time customer from a higher-RTO marketing cohort"
        )

    # --------------------------------------
    # RULE 8: Default decision
    # --------------------------------------

    return (
        "ship as-is",
        "No additional risk condition identified"
    )


# ==========================================
# 8. APPLY INITIAL DECISIONS
# ==========================================

results = df.apply(make_decision, axis=1)

df["decision"] = results.apply(
    lambda x: x[0]
)

df["reason"] = results.apply(
    lambda x: x[1]
)


# ==========================================
# 9. INITIAL CUSTOMER RESPONSE
# ==========================================

# No actual customer responses are available
# at the time of initial decision generation.

df["customer_response"] = "PENDING"


# ==========================================
# 10. DETERMINE INITIAL FINAL ACTION
# ==========================================

def determine_initial_action(row):

    decision = row["decision"]

    # Ship without additional verification
    if decision == "ship as-is":

        return (
            "SHIP",
            "No additional verification required"
        )

    # Prepaid conversion request
    elif decision == "nudge to prepaid":

        return (
            "WAITING_FOR_CUSTOMER",
            "Waiting for prepaid payment decision"
        )

    # WhatsApp confirmation required
    elif decision == "ship after WhatsApp confirmation":

        return (
            "WAITING_FOR_CUSTOMER",
            "Waiting for WhatsApp confirmation"
        )

    # Hold for human review
    elif decision == "hold/cancel":

        return (
            "HOLD_FOR_MANUAL_REVIEW",
            "Customer history inconsistency requires manual review"
        )

    # Unknown decisions are also held safely
    else:

        return (
            "HOLD_FOR_MANUAL_REVIEW",
            "Unknown decision requires manual review"
        )


actions = df.apply(
    determine_initial_action,
    axis=1
)

df["final_action"] = actions.apply(
    lambda x: x[0]
)

df["final_action_reason"] = actions.apply(
    lambda x: x[1]
)


# ==========================================
# 11. DECISION SUMMARY
# ==========================================

print("\n========== INITIAL DECISION SUMMARY ==========")

decision_summary = (
    df["decision"]
    .value_counts()
)

print(decision_summary.to_string())


print("\n========== INITIAL FINAL ACTION SUMMARY ==========")

action_summary = (
    df["final_action"]
    .value_counts()
)

print(action_summary.to_string())


# ==========================================
# 12. CHECK FOUR DECISION CATEGORIES
# ==========================================

expected_decisions = [
    "ship as-is",
    "ship after WhatsApp confirmation",
    "nudge to prepaid",
    "hold/cancel"
]

print("\n========== FOUR-CATEGORY CHECK ==========")

for decision in expected_decisions:

    count = int(
        (df["decision"] == decision).sum()
    )

    print(f"{decision}: {count}")


# ==========================================
# 13. DISPLAY SAMPLE DECISIONS
# ==========================================

print("\n========== SAMPLE DECISIONS ==========")

print(
    df[
        [
            "order_id",
            "decision",
            "reason",
            "customer_response",
            "final_action",
            "final_action_reason"
        ]
    ]
    .head(15)
    .to_string(index=False)
)


# ==========================================
# 14. SAVE DECISION LOG
# ==========================================

df.to_csv(
    "decision_log.csv",
    index=False
)

print("\nDecision log saved successfully.")
print("Output file: decision_log.csv")


# ==========================================
# 15. IMPORTANT NOTES
# ==========================================

print("""
IMPORTANT NOTES:

1. The engine generates four initial decision categories.
2. HOLD_FOR_MANUAL_REVIEW is not automatic cancellation.
3. Inconsistent customer history requires human verification.
4. Invalid phone or pincode information triggers
   WhatsApp confirmation, not automatic rejection.
5. Customer responses are initially marked PENDING.
6. Historical final_status is not used by the decision rules.
""")
