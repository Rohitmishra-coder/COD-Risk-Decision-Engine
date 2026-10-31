
import pandas as pd

# Load original dataset
df = pd.read_csv("orders_sample.csv", dtype={"phone": str})

# Remove exact duplicates
df = df.drop_duplicates().copy()

# Normalize status
df["status_norm"] = (
    df["final_status"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Keep final outcomes only
df = df[
    df["status_norm"].isin(["DELIVERED", "RTO"])
].copy()

df["is_rto"] = (df["status_norm"] == "RTO").astype(int)


# =================================
# 1. CUSTOMER ORDER HISTORY
# =================================

print("\n===== CUSTOMER PRIOR ORDERS =====")

history = (
    df.groupby("customer_prior_orders")
    .agg(
        total_orders=("is_rto", "count"),
        total_rto=("is_rto", "sum"),
        rto_rate=("is_rto", "mean")
    )
)

history["rto_rate"] *= 100

print(history.round(2))


# =================================
# 2. ORDER VALUE ANALYSIS
# =================================

print("\n===== ORDER VALUE ANALYSIS =====")

bins = [0, 400, 650, 1000, 1500, float("inf")]

labels = [
    "0-399",
    "400-649",
    "650-999",
    "1000-1499",
    "1500+"
]

df["order_value_group"] = pd.cut(
    df["order_value"],
    bins=bins,
    labels=labels,
    right=False
)

value_stats = (
    df.groupby("order_value_group", observed=False)
    .agg(
        total_orders=("is_rto", "count"),
        total_rto=("is_rto", "sum"),
        rto_rate=("is_rto", "mean")
    )
)

value_stats["rto_rate"] *= 100

print(value_stats.round(2))


# =================================
# 3. CITY ANALYSIS
# =================================

print("\n===== CITY ANALYSIS =====")

city_stats = (
    df.groupby("city")
    .agg(
        total_orders=("is_rto", "count"),
        total_rto=("is_rto", "sum"),
        rto_rate=("is_rto", "mean")
    )
)

city_stats["rto_rate"] *= 100

# Only cities with at least 30 orders
city_stats = city_stats[
    city_stats["total_orders"] >= 30
]

print(
    city_stats.sort_values(
        "rto_rate",
        ascending=False
    ).round(2)
)


# =================================
# 4. PHONE NUMBER VALIDATION
# =================================

print("\n===== PHONE VALIDATION =====")

phone_digits = (
    df["phone"]
    .astype("string")
    .str.replace(r"\D", "", regex=True)
)

invalid_phone = (
    phone_digits.str.len() != 10
).fillna(True)

print("Invalid phone numbers:", invalid_phone.sum())

# Do not print actual phone numbers.


# =================================
# 5. PINCODE VALIDATION
# =================================

print("\n===== PINCODE VALIDATION =====")

pincode_numeric = pd.to_numeric(
    df["pincode"],
    errors="coerce"
)

valid_pincode = (
    pincode_numeric.notna()
    & pincode_numeric.mod(1).eq(0)
    & pincode_numeric.between(100000, 999999)
)

print("Missing pincodes:", df["pincode"].isna().sum())

print(
    "Invalid non-missing pincodes:",
    (~valid_pincode & df["pincode"].notna()).sum()
)


# =================================
# 6. CUSTOMER HISTORY VALIDATION
# =================================

print("\n===== CUSTOMER HISTORY VALIDATION =====")

invalid_history = (
    df["customer_prior_rto"]
    > df["customer_prior_orders"]
)

print(
    "Records where prior RTOs exceed prior orders:",
    invalid_history.sum()
)


# =================================
# 7. ORDER VALUE VALIDATION
# =================================

print("\n===== ORDER VALUE VALIDATION =====")

print(
    "Zero or negative order values:",
    (df["order_value"] <= 0).sum()
)


# =================================
# 8. DATE VALIDATION
# =================================

print("\n===== DATE VALIDATION =====")

dates = pd.to_datetime(
    df["order_datetime"],
    errors="coerce"
)

print("Invalid dates:", dates.isna().sum())

print("Earliest order:", dates.min())
print("Latest order:", dates.max())


print("\n===== ANALYSIS COMPLETED =====")
