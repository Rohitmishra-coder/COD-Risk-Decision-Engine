import pandas as pd

# Assignment assumptions
RTO_COST = 169.40
GROSS_MARGIN = 0.62
PREPAID_RTO_RATE = 0.04
PREPAID_DISCOUNT = 20

# Illustrative conversion scenarios
CONVERSION_RATES = [0.10, 0.20, 0.30]

# Load historical decisions
df = pd.read_csv("decision_log.csv")

df["final_status"] = df["final_status"].str.upper().str.strip()

# Only evaluate historical COD orders with final outcomes
df = df[
    df["final_status"].isin(["DELIVERED", "RTO"])
].copy()

# Select prepaid-nudge group
nudges = df[df["decision"] == "nudge to prepaid"].copy()

# Use actual order values
nudges["order_value"] = pd.to_numeric(
    nudges["order_value"], errors="coerce"
)

# Exclude invalid order values from financial simulation
nudges = nudges[nudges["order_value"] > 0].copy()

# Historical COD RTO rate in this group
cod_rto_rate = (
    nudges["final_status"].eq("RTO").mean()
)

print("Orders eligible for prepaid simulation:", len(nudges))
print("Historical COD RTO rate:", round(cod_rto_rate * 100, 2), "%")

print("\n===== PREPAID CONVERSION SCENARIOS =====")

for conversion_rate in CONVERSION_RATES:

    converted_orders = len(nudges) * conversion_rate

    # Difference in RTO probability after prepaid conversion
    rto_reduction = cod_rto_rate - PREPAID_RTO_RATE

    # Expected RTOs prevented
    expected_rtos_prevented = (
        converted_orders * rto_reduction
    )

    # Expected RTO cost avoided
    rto_cost_saved = (
        expected_rtos_prevented * RTO_COST
    )

    # Additional delivered gross margin
    avg_order_value = nudges["order_value"].mean()

    additional_margin = (
        expected_rtos_prevented
        * avg_order_value
        * GROSS_MARGIN
    )

    # Discount is paid for every converted order
    discount_cost = (
        converted_orders * PREPAID_DISCOUNT
    )

    # Estimated incremental impact
    net_impact = (
        rto_cost_saved
        + additional_margin
        - discount_cost
    )

    print(f"\nConversion rate: {conversion_rate * 100:.0f}%")
    print(f"Expected converted orders: {converted_orders:.1f}")
    print(f"Expected RTOs prevented: {expected_rtos_prevented:.1f}")
    print(f"RTO cost avoided: ₹{rto_cost_saved:,.2f}")
    print(f"Additional gross margin: ₹{additional_margin:,.2f}")
    print(f"Discount expense: ₹{discount_cost:,.2f}")
    print(f"Estimated net impact: ₹{net_impact:,.2f}")