import json
import os
import pandas as pd

# Define expected indicators
USD_INDICATORS = ["FEDFUNDS", "CPIAUCSL", "GDP", "UNRATE", "NAPM"]
# Map ONS series IDs to meaningful names for filenames and keys
ONS_INDICATORS_MAP = {
    "L55O": "CPIH",
    "D7G7": "CPI",
    "IHYQ": "GDP_Dataset",  # Note: Processing for 'dataset' types might be more complex
    "MGSX": "Unemployment_Dataset" # Note: Processing for 'dataset' types might be more complex
}

# Base data directory (assuming script is in 'scripts/' and data in 'data/')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")

def load_and_process_fred_data(indicator_code, data_dir=DATA_DIR):
    """
    Loads and processes FRED data for a given indicator code.
    Converts observations to a Pandas DataFrame with 'date' and 'value'.
    """
    filename = os.path.join(data_dir, f"USD_{indicator_code}.json")
    print(f"Processing FRED data for {indicator_code} from {filename}...")

    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"  Error: File not found: {filename}")
        return pd.DataFrame()
    except json.JSONDecodeError:
        print(f"  Error: Invalid JSON in file: {filename}")
        return pd.DataFrame()

    if 'observations' not in data or not data['observations']:
        print(f"  Warning: 'observations' key missing or empty in {filename}.")
        return pd.DataFrame()

    df = pd.DataFrame(data['observations'])

    # Keep only relevant columns if others exist (like 'realtime_start', 'realtime_end')
    if 'date' not in df.columns or 'value' not in df.columns:
        print(f"  Error: 'date' or 'value' column missing in observations for {filename}.")
        return pd.DataFrame()

    df = df[['date', 'value']]

    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    # FRED uses '.' for missing data, which to_numeric handles well with errors='coerce'
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    df = df.dropna(subset=['date']) # Remove rows where date conversion failed
    df = df.set_index('date')
    df = df.sort_index()

    print(f"  Successfully processed {indicator_code}. Shape: {df.shape}")
    return df

def load_and_process_ons_data(ons_series_id, indicator_name, data_dir=DATA_DIR):
    """
    Loads and processes ONS data for a given ONS series ID and indicator name.
    Attempts to parse common ONS timeseries structures.
    """
    filename = os.path.join(data_dir, f"GBP_{indicator_name}.json") # e.g. GBP_CPIH.json
    print(f"Processing ONS data for {indicator_name} ({ons_series_id}) from {filename}...")

    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"  Error: File not found: {filename}")
        return pd.DataFrame()
    except json.JSONDecodeError:
        print(f"  Error: Invalid JSON in file: {filename}")
        return pd.DataFrame()

    # ONS data structure varies. This is a common pattern for timeseries.
    # It might be a list of dictionaries, or a dictionary with a key like 'months', 'quarters', 'years'.
    observations = []
    if isinstance(data, list): # e.g. some direct timeseries might be a list
        observations = data
    elif isinstance(data, dict):
        # Try common keys for timeseries data arrays
        for key in ['observations', 'months', 'quarters', 'years', 'data', 'timeseries', 'value']:
            if key in data and isinstance(data[key], list):
                observations = data[key]
                break
        if not observations and 'description' in data and 'releaseDate' in data: # CPI/CPIH like
             if 'months' in data: observations = data['months'] # CPIH has 'months'
             elif 'years' in data: observations = data['years'] # some series have 'years'
             elif 'quarters' in data: observations = data['quarters'] # some series have 'quarters'

    if not observations:
        print(f"  Warning: Could not find a list of observations in {filename} for {indicator_name}.")
        print(f"  Data keys found: {list(data.keys()) if isinstance(data, dict) else 'Data is a list'}")
        # For Datasets like IHYQ (GDP) or MGSX (Unemployment), the structure is often more complex.
        # The initial fetch might return metadata or links to specific versions/editions.
        # This function may need significant refinement once actual dataset file structures are known.
        if indicator_name in ["GDP_Dataset", "Unemployment_Dataset"]:
            print(f"  Note: {indicator_name} is a dataset. The loaded JSON might contain metadata or links. Specific series extraction logic will be needed if this file does not contain direct observations.")
        return pd.DataFrame()

    df = pd.DataFrame(observations)

    # Rename columns: ONS uses 'date', 'value', 'month', 'year', 'quarter', etc.
    # We need to standardize to 'date' and 'value'.
    if 'date' not in df.columns:
        if ' kawaida' in df.columns: # Placeholder for actual date field in dataset if different
             df.rename(columns={'kawaida': 'date'}, inplace=True) # Example for a dataset specific date field
        # CPI/CPIH specific structure
        elif 'year' in df.columns and 'month' in df.columns:
            df['date_str'] = df['year'] + '-' + df['month']
            df['date'] = pd.to_datetime(df['date_str'], errors='coerce')
        elif 'year' in df.columns and 'quarter' in df.columns: # e.g. Q1, Q2
            # Simplistic: take first month of quarter. More precise handling might be needed.
            df['month_num'] = df['quarter'].str.replace('Q', '').astype(int) * 3 - 2
            df['date_str'] = df['year'] + '-' + df['month_num'].astype(str).str.zfill(2)
            df['date'] = pd.to_datetime(df['date_str'], errors='coerce')
        # Add more date column detection logic as ONS structures are explored
        else:
            print(f"  Error: No 'date' column or recognizable date components (year/month/quarter) in {filename} for {indicator_name}.")
            return pd.DataFrame()

    if 'value' not in df.columns:
         # CPI/CPIH specific structure
        if 'value' not in df.columns and 'valueString' in df.columns : # some ONS data has valueString
            df.rename(columns={'valueString': 'value'}, inplace=True)
        else:
            print(f"  Error: No 'value' column in {filename} for {indicator_name}.")
            return pd.DataFrame()

    df = df[['date', 'value']]
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['value'] = pd.to_numeric(df['value'], errors='coerce')

    df = df.dropna(subset=['date', 'value']) # Drop rows where essential data is missing/unparseable
    df = df.set_index('date')
    df = df.sort_index()

    print(f"  Successfully processed {indicator_name}. Shape: {df.shape}")
    return df

if __name__ == "__main__":
    processed_data_store = {}

    print("--- Processing USD (FRED) Data ---")
    for indicator in USD_INDICATORS:
        df = load_and_process_fred_data(indicator)
        if not df.empty:
            processed_data_store[f"USD_{indicator}"] = df
            print(f"  {indicator} DataFrame Head:")
            print(df.head())
            print(f"  {indicator} DataFrame Info:")
            df.info()
            print("-" * 40)
        else:
            print(f"  Failed to load or process {indicator}.\n" + "-"*40)

    print("\n--- Processing GBP (ONS) Data ---")
    for ons_id, name in ONS_INDICATORS_MAP.items():
        df = load_and_process_ons_data(ons_id, name)
        if not df.empty:
            processed_data_store[f"GBP_{name}"] = df
            print(f"  {name} ({ons_id}) DataFrame Head:")
            print(df.head())
            print(f"  {name} ({ons_id}) DataFrame Info:")
            df.info()
            print("-" * 40)
        else:
            print(f"  Failed to load or process {name} ({ons_id}).\n" + "-"*40)

    print("\nAll data processing attempts complete.")
    print(f"Total DataFrames in store: {len(processed_data_store)}")

    # Further steps could involve saving these DataFrames:
    # PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    # if not os.path.exists(PROCESSED_DATA_DIR):
    #     os.makedirs(PROCESSED_DATA_DIR)
    # for name, df in processed_data_store.items():
    #     df.to_csv(os.path.join(PROCESSED_DATA_DIR, f"{name}.csv"))
    # print(f"Processed data saved to {PROCESSED_DATA_DIR}")
