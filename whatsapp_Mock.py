
import pandas as pd
from datetime import datetime

# ==========================================
# 1. LOAD DECISION LOG
# ==========================================

df = pd.read_csv("decision_log.csv")

# Select orders requiring customer interaction
prepaid_orders = df[
    df["decision"] == "nudge to prepaid"
].copy()

confirmation_orders = df[
    df["decision"] == "ship after WhatsApp confirmation"
].copy()


# ==========================================
# 2. PROCESS CUSTOMER RESPONSE
# ==========================================

def process_response(response, decision):

    response = str(response).strip().upper()

    if response == "YES":

        if decision == "nudge to prepaid":
            return (
                "SEND_PREPAID_LINK",
                "PREPAID_LINK_SENT",
                "Customer agreed to receive prepaid payment link"
            )

        return (
            "CONFIRM_COD_ORDER",
            "SHIP",
            "Customer confirmed the COD order"
        )

    elif response == "NO":

        if decision == "nudge to prepaid":
            return (
                "KEEP_COD",
                "KEEP_COD",
                "Customer declined prepaid payment"
            )

        return (
            "HOLD_FOR_MANUAL_REVIEW",
            "HOLD_FOR_MANUAL_REVIEW",
            "Customer declined COD order confirmation"
        )

    else:

        return (
            "ASK_FOR_VALID_RESPONSE",
            "WAITING_FOR_CUSTOMER",
            "Invalid response; waiting for a valid response"
        )


# ==========================================
# 3. PROCESS 24-HOUR TIMEOUT
# ==========================================

def process_timeout(decision):

    if decision == "nudge to prepaid":

        return (
            "KEEP_COD",
            "KEEP_COD",
            "No prepaid response within 24 hours; retain COD"
        )

    return (
        "HOLD_FOR_MANUAL_REVIEW",
        "HOLD_FOR_MANUAL_REVIEW",
        "No COD confirmation within 24 hours"
    )


# ==========================================
# 4. PREPARE TEST CASES
# ==========================================

# Test three prepaid-nudge orders
prepaid_samples = prepaid_orders.head(3)

# Test two WhatsApp-confirmation orders
confirmation_samples = confirmation_orders.head(2)

sample_orders = pd.concat(
    [prepaid_samples, confirmation_samples]
)

test_responses = [
    "YES",
    "NO",
    "HELLO",
    "YES",
    "NO"
]

interaction_logs = []


# ==========================================
# 5. SIMULATE CUSTOMER RESPONSES
# ==========================================

for (_, order), response in zip(
    sample_orders.iterrows(),
    test_responses
):

    system_action, final_action, reason = process_response(
        response,
        order["decision"]
    )

    interaction_time = datetime.now().isoformat(
        timespec="seconds"
    )

    interaction_logs.append({
        "order_id": order["order_id"],
        "decision": order["decision"],
        "customer_response": response,
        "response_time": interaction_time,
        "system_action": system_action,
        "final_action": final_action,
        "final_action_reason": reason,
        "interaction_status": (
            "AWAITING_VALID_RESPONSE"
            if system_action == "ASK_FOR_VALID_RESPONSE"
            else "COMPLETED"
        )
    })


# ==========================================
# 6. SIMULATE ONE 24-HOUR TIMEOUT
# ==========================================

# Prefer a WhatsApp-confirmation order for timeout testing
if len(confirmation_orders) > 2:

    timeout_order = confirmation_orders.iloc[2]

elif len(prepaid_orders) > 3:

    timeout_order = prepaid_orders.iloc[3]

else:

    timeout_order = None


if timeout_order is not None:

    system_action, final_action, reason = process_timeout(
        timeout_order["decision"]
    )

    interaction_logs.append({
        "order_id": timeout_order["order_id"],
        "decision": timeout_order["decision"],
        "customer_response": "NO RESPONSE",
        "response_time": "",
        "system_action": system_action,
        "final_action": final_action,
        "final_action_reason": reason,
        "interaction_status": "TIMED_OUT"
    })


# ==========================================
# 7. CREATE INTERACTION LOG
# ==========================================

interaction_df = pd.DataFrame(interaction_logs)

interaction_df.to_csv(
    "whatsapp_interaction_log.csv",
    index=False
)


# ==========================================
# 8. UPDATE DECISION LOG
# ==========================================

for _, interaction in interaction_df.iterrows():

    order_id = interaction["order_id"]

    matching_rows = df["order_id"] == order_id

    df.loc[
        matching_rows,
        "customer_response"
    ] = interaction["customer_response"]

    df.loc[
        matching_rows,
        "final_action"
    ] = interaction["final_action"]

    df.loc[
        matching_rows,
        "final_action_reason"
    ] = interaction["final_action_reason"]


# Save updated decision log
df.to_csv(
    "decision_log.csv",
    index=False
)


# ==========================================
# 9. DISPLAY RESULTS
# ==========================================

print("\n===== WHATSAPP INTERACTION LOG =====")

print(
    interaction_df.to_string(index=False)
)


print("\n===== UPDATED FINAL ACTION SUMMARY =====")

print(
    df["final_action"].value_counts()
)


print("\n===== UPDATED CUSTOMER RESPONSE SUMMARY =====")

print(
    df["customer_response"].value_counts()
)


print("\nInteraction log saved successfully.")

print("Decision log updated successfully.")
