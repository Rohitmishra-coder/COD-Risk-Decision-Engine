
import pandas as pd


df = pd.read_csv("orders_sample.csv", dtype={"phone": str})

print("\n========== ORIGINAL DATA ==========")

print("Total rows:", len(df))
print("Total columns:", len(df.columns))

print("\nColumn names:")
print(df.columns.tolist())




print("\n========= DATA TYPES ==========")

print(df.dtypes)




print("\n========== MISSING VALUES ==========")

print(df.isnull().sum())


print("\n========== DUPLICATE CHECK ==========")

print("Duplicate full rows:", df.duplicated().sum())

print("Duplicate order IDs:",
      df["order_id"].duplicated().sum())

# Remove only exact duplicate rows
df = df.drop_duplicates().copy()

print("Rows after removing exact duplicates:", len(df))


df["status_norm"] = (
    df["final_status"]
    .astype(str)
    .str.strip()
    .str.upper()
)

print("\n========== ORDER STATUS ==========")

print(df["status_norm"].value_counts())


# Keep only known final outcomes
valid = df[
    df["status_norm"].isin(["DELIVERED", "RTO"])
].copy()

valid["is_rto"] = (
    valid["status_norm"] == "RTO"
).astype(int)


total = len(valid)
rto_count = valid["is_rto"].sum()
delivered_count = total - rto_count

rto_rate = (rto_count / total) * 100

print("\n========== OVERALL RTO ANALYSIS ==========")

print("Valid orders:", total)
print("Delivered:", delivered_count)
print("RTO:", rto_count)

print(f"RTO Rate: {rto_rate:.2f}%")

print("\n========== RTO BY PRIOR RTO HISTORY ==========")

history = (
    valid.groupby("customer_prior_rto")
    .agg(
        orders=("is_rto", "count"),
        rtos=("is_rto", "sum"),
        rto_rate=("is_rto", "mean")
    )
)

history["rto_rate"] = (
    history["rto_rate"] * 100
).round(2)

print(history)


print("\n========== RTO BY COURIER ==========")

courier_stats = (
    valid.groupby("courier")
    .agg(
        orders=("is_rto", "count"),
        rtos=("is_rto", "sum"),
        rto_rate=("is_rto", "mean")
    )
)

courier_stats["rto_rate"] = (
    courier_stats["rto_rate"] * 100
).round(2)

print(courier_stats.sort_values("rto_rate", ascending=False))


# ----------------------------------
# 9. ANALYSE MARKETING SOURCES
# ----------------------------------

print("\n========== RTO BY MARKETING SOURCE ==========")

source_stats = (
    valid.groupby("utm_source")
    .agg(
        orders=("is_rto", "count"),
        rtos=("is_rto", "sum"),
        rto_rate=("is_rto", "mean")
    )
)

source_stats["rto_rate"] = (
    source_stats["rto_rate"] * 100
).round(2)

print(source_stats.sort_values("rto_rate", ascending=False))




valid.to_csv("cleaned_orders.csv", index=False)

print("\nCleaned dataset saved successfully!")
