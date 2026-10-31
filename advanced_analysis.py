
import pandas as pd

# Load and clean basic records
df = pd.read_csv("orders_sample.csv", dtype={"phone": str})

df = df.drop_duplicates().copy()

df["status_norm"] = (
    df["final_status"].astype(str).str.strip().str.upper()
)

df = df[
    df["status_norm"].isin(["DELIVERED", "RTO"])
].copy()

df["is_rto"] = (df["status_norm"] == "RTO").astype(int)



print("\n===== PRIOR ORDERS VS PRIOR RTO =====")

history = (
    df.groupby(
        ["customer_prior_orders", "customer_prior_rto"]
    )
    .agg(
        orders=("is_rto", "count"),
        rtos=("is_rto", "sum"),
        rto_rate=("is_rto", "mean")
    )
)

history["rto_rate"] *= 100

print(history.round(2).to_string())



print("\n===== INVALID CUSTOMER HISTORY =====")

invalid_history = df[
    df["customer_prior_rto"]
    > df["customer_prior_orders"]
]

print("Invalid records:", len(invalid_history))

# Show only non-sensitive information
print(
    invalid_history[
        [
            "order_id",
            "customer_prior_orders",
            "customer_prior_rto",
            "final_status"
        ]
    ].to_string(index=False)
)




print("\n===== CITY AND COURIER ANALYSIS =====")

city_courier = (
    df.groupby(["city", "courier"])
    .agg(
        orders=("is_rto", "count"),
        rtos=("is_rto", "sum"),
        rto_rate=("is_rto", "mean")
    )
    .reset_index()
)

city_courier["rto_rate"] *= 100

# Only show groups with at least 10 orders
city_courier = city_courier[
    city_courier["orders"] >= 10
]

print(
    city_courier.sort_values(
        "rto_rate",
        ascending=False
    ).round(2).to_string(index=False)
)




print("\n===== SOURCE VS FIRST-TIME CUSTOMERS =====")

df["customer_type"] = (
    df["customer_prior_orders"]
    .apply(lambda x: "First-time" if x == 0 else "Returning")
)

source_customer = (
    df.groupby(["utm_source", "customer_type"])
    .agg(
        orders=("is_rto", "count"),
        rtos=("is_rto", "sum"),
        rto_rate=("is_rto", "mean")
    )
)

source_customer["rto_rate"] *= 100

print(source_customer.round(2).to_string())



print("\n===== PREVIOUS CUSTOMER RTO RATE =====")

df["previous_rto_rate"] = (
    df["customer_prior_rto"]
    / df["customer_prior_orders"].replace(0, pd.NA)
)

print(
    df[
        [
            "customer_prior_orders",
            "customer_prior_rto",
            "previous_rto_rate",
            "is_rto"
        ]
    ].head(15).to_string(index=False)
)




print("\n===== ZERO ORDER VALUE RECORDS =====")

zero_orders = df[df["order_value"] <= 0]

print("Records:", len(zero_orders))

print(
    zero_orders[
        ["order_id", "order_value", "num_items", "final_status"]
    ].to_string(index=False)
)


print("\n===== ADVANCED ANALYSIS COMPLETED =====")
