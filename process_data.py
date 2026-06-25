import os
import glob
import sqlite3
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)

engine = create_engine("sqlite:///bluestock_mf.db")
print("⚡ Starting Day 2 ETL Processing Pipeline...\n")

try:
    print("⏳ Processing nav_history.csv...")
    import glob
    raw_schemes = glob.glob(f"{RAW_DIR}/*_raw.csv")
    df_nav = pd.concat([pd.read_csv(f) for f in raw_schemes]) if raw_schemes else pd.DataFrame(columns=["date", "nav", "scheme_code"])
    if "scheme_code" in df_nav.columns and "amfi_code" not in df_nav.columns:
        df_nav.rename(columns={"scheme_code": "amfi_code"}, inplace=True)
    df_nav["date"] = pd.to_datetime(df_nav["date"], format="%d-%m-%Y", errors="coerce")
    df_nav = df_nav.dropna(subset=["date", "amfi_code"])
    df_nav["nav"] = pd.to_numeric(df_nav["nav"], errors="coerce")
    df_nav = df_nav[df_nav["nav"] > 0]
    df_nav.drop_duplicates(subset=["amfi_code", "date"], inplace=True)
    df_nav.sort_values(by=["amfi_code", "date"], inplace=True)
    df_nav = df_nav.set_index("date").groupby("amfi_code", group_keys=False).resample("D").ffill().reset_index()
    df_nav.to_csv(f"{PROCESSED_DIR}/cleaned_nav_history.csv", index=False)
    df_nav.to_sql("fact_nav", engine, if_exists="replace", index=False)
    print(f"✅ Loaded 'fact_nav': {len(df_nav)} rows.")
except Exception as e:
    print(f"❌ Error processing NAV history: {e}")

try:
    print("\n⏳ Processing investor_transactions.csv...")
    mock_tx = pd.DataFrame({
        "transaction_id": range(1, 101),
        "amfi_code": np.random.choice([125497, 119551, 120503, 118632, 119092, 120841], 100),
        "transaction_type": np.random.choice(["sip", "Lumpsum", "REDEMPTION"], 100),
        "amount": np.random.uniform(100, 50000, 100),
        "transaction_date": pd.date_range(start="2026-01-01", periods=100, freq="D").strftime("%Y-%m-%d"),
        "kyc_status": np.random.choice(["Verified", "Pending", "Failed"], 100),
        "state": np.random.choice(["Maharashtra", "Tamil Nadu", "Karnataka", "Delhi", "Gujarat"], 100)
    })
    mock_tx.to_csv(f"{RAW_DIR}/investor_transactions.csv", index=False)
    df_tx = pd.read_csv(f"{RAW_DIR}/investor_transactions.csv")
    df_tx["transaction_date"] = pd.to_datetime(df_tx["transaction_date"], errors="coerce")
    df_tx["amount"] = pd.to_numeric(df_tx["amount"], errors="coerce")
    df_tx = df_tx[df_tx["amount"] > 0]
    df_tx["transaction_type"] = df_tx["transaction_type"].astype(str).str.upper().str.strip()
    tx_map = {"SIP": "SIP", "LUMPSUM": "Lumpsum", "REDEMPTION": "Redemption"}
    df_tx["transaction_type"] = df_tx["transaction_type"].map(tx_map).fillna("Lumpsum")
    df_tx.to_csv(f"{PROCESSED_DIR}/cleaned_investor_transactions.csv", index=False)
    df_tx.to_sql("fact_transactions", engine, if_exists="replace", index=False)
    print(f"✅ Loaded 'fact_transactions': {len(df_tx)} rows.")
except Exception as e:
    print(f"❌ Error processing transactions: {e}")

try:
    print("\n⏳ Processing scheme_performance.csv...")
    mock_perf = pd.DataFrame({
        "amfi_code": [125497, 119551, 120503, 118632, 119092, 120841],
        "scheme_name": ["HDFC Top 100", "SBI Bluechip", "ICICI Bluechip", "Nippon Large Cap", "Axis Bluechip", "Kotak Bluechip"],
        "returns_1y": [12.5, 14.2, 13.0, 11.8, 9.5, 15.1],
        "expense_ratio": [0.005, 0.012, 0.022, 0.018, 0.002, 0.021],
        "aum": [450000000, 320000000, 510000000, 280000000, 620000000, 190000000]
    })
    mock_perf.to_csv(f"{RAW_DIR}/scheme_performance.csv", index=False)
    df_perf = pd.read_csv(f"{RAW_DIR}/scheme_performance.csv")
    df_perf["returns_1y"] = pd.to_numeric(df_perf["returns_1y"], errors="coerce").fillna(0.0)
    df_perf["expense_ratio"] = pd.to_numeric(df_perf["expense_ratio"], errors="coerce").clip(0.001, 0.025)
    df_perf["anomaly_flag"] = np.where((df_perf["returns_1y"] > 50) | (df_perf["returns_1y"] < -30), 1, 0)
    df_perf.to_csv(f"{PROCESSED_DIR}/cleaned_scheme_performance.csv", index=False)
    df_perf[["amfi_code", "scheme_name"]].drop_duplicates().to_sql("dim_fund", engine, if_exists="replace", index=False)
    df_perf.to_sql("fact_performance", engine, if_exists="replace", index=False)
    print("✅ Loaded 'dim_fund' and 'fact_performance' components.")
except Exception as e:
    print(f"❌ Error processing performance data: {e}")

print("\n🚀 Day 2 Data Pipeline Execution Complete! Files stored in database 'bluestock_mf.db'.")
