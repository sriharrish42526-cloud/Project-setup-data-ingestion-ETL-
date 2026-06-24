cat << 'EOF' > ingest_data.py
import os
import glob
import pandas as pd
import requests

os.makedirs("data/raw", exist_ok=True)

print("\n## 1. Profiling Local CSV Datasets ##\n")
csv_files = glob.glob("*.csv") + glob.glob("data/raw/*.csv")
csv_files = list(set([f for f in csv_files if "requirements.txt" not in f and "ingest_data.py" not in f]))[:10]

if not csv_files:
    print("⚠️ No local CSV files found to profile. Place your 10 datasets in 'data/raw/'.")
else:
    for file in csv_files:
        print(f"📄 Dataset: {file}")
        print("-" * 40)
        try:
            df = pd.read_csv(file)
            print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
            print("\nData Types:")
            print(df.dtypes)
            print("\nFirst 3 Rows:")
            print(df.head(3))
        except Exception as e:
            print(f"❌ Error: {e}")

print("\n## 2. Fetching Live & Historical NAV Data ##\n")
schemes = {
    "125497": "HDFC_Top_100_Direct", 
    "119551": "SBI_Bluechip", 
    "120503": "ICICI_Bluechip", 
    "118632": "Nippon_Large_Cap", 
    "119092": "Axis_Bluechip", 
    "120841": "Kotak_Bluechip"
}

for code, name in schemes.items():
    url = f"https://api.mfapi.in/mf/{code}"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            nav_list = data.get("data", [])
            if nav_list:
                df_nav = pd.DataFrame(nav_list)
                df_nav["scheme_code"] = code
                df_nav["scheme_name"] = data.get("meta", {}).get("scheme_name", name)
                output_path = f"data/raw/{name}_raw.csv"
                df_nav.to_csv(output_path, index=False)
                print(f"✅ Saved {name} -> {output_path}")
    except Exception as e:
        print(f"❌ Error fetching {code}: {e}")
EOF