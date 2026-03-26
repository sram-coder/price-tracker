#Author: Sharanya Ram
import pandas as pd
import glob
import numpy as np
import matplotlib.pyplot as plt
import os

os.makedirs("outputs", exist_ok=True)

# Get all CSV files from products_data
csv_files = sorted(glob.glob("products_data/*.csv"))

if not csv_files:
    print("No CSV files found")
    exit()

# Read and combine!
df_list = [pd.read_csv(file) for file in csv_files]
uncleaned_combined_df = pd.concat(df_list, ignore_index=True)
combined_df = pd.concat(df_list, ignore_index=True)

# Clean!
combined_df = combined_df[combined_df["price"] > 0]
combined_df = combined_df[(combined_df["price"] > 0) & (combined_df["price"] < 10000)]
combined_df["date"] = pd.to_datetime(
    combined_df["date"],
    format="ISO8601",
    errors="coerce",
    utc=True)

combined_df["price"] = pd.to_numeric(combined_df["price"], errors="coerce")
combined_df["name"] = combined_df["name"].str.strip()
combined_df = combined_df.dropna(subset=["price", "date", "name"])
combined_df = combined_df.drop_duplicates(subset=["name", "site", "date"])
combined_df = combined_df.sort_values(by=["model", "date"])

#check, raise error if not cleaned properly
required_cols = ["price", "date", "name"]
for col in required_cols:
    if col not in combined_df.columns:
        raise ValueError(f"Missing column: {col}")

#Clear bad values
print(f"Rows before cleaning: {len(uncleaned_combined_df)}")
print(f"Rows after cleaning: {len(combined_df)}")
print("Missing price:", uncleaned_combined_df["price"].isna().sum())
print("Missing date:", uncleaned_combined_df["date"].isna().sum())
print("Missing name:", uncleaned_combined_df["name"].isna().sum())
print("Duplicates from same date:", uncleaned_combined_df.duplicated(subset=["name", "site", "date"]).sum())
combined_df.to_csv("outputs/combined_cleaned.csv", index=False)

# Get unique models
models = combined_df["model"].unique()

plt.style.use('seaborn-v0_8')
plt.title("Price Trends Over Time", fontsize=20, weight='bold')
plt.xlabel("Date", fontsize=14)
plt.tight_layout()
plt.ylabel("Price ($)", fontsize=14)
plt.figure(figsize=(10, 6), dpi=120)
plt.plot(linewidth=4, marker='o', markersize=5)
plt.plot(color='#4C72B0')
plt.tight_layout()
ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

count = 0

combined_df["date"] = pd.to_datetime(combined_df["date"]).dt.floor("D")
combined_df = combined_df.sort_values("date")

for model, model_df in combined_df.groupby("model"):

    plt.figure(figsize=(10, 6))

    full_range = pd.date_range(
        start=model_df["date"].min(),
        end=model_df["date"].max(),
        freq="D"
    )

    for site, site_df in model_df.groupby("site"):

        site_df = site_df.copy()

        daily_avg = (
            site_df
            .set_index("date")
            .groupby("date")["price"]
            .mean()
        )

        daily_avg = daily_avg.reindex(full_range)

        daily_avg = daily_avg.ffill()

        # skip if still empty
        if daily_avg.isna().all():
            continue

        plt.plot(full_range, daily_avg.values, label=site)

    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"outputs/price_trend_{count}.png")
    plt.close()

    count += 1

