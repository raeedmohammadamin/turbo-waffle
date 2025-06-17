import matplotlib.pyplot as plt
import os
import sys

# Add the script's directory to sys.path to allow importing process_data
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

try:
    from process_data import load_and_process_fred_data, load_and_process_ons_data, ONS_INDICATORS_MAP
except ImportError as e:
    print(f"Error importing from process_data: {e}")
    print("Ensure process_data.py is in the same directory (scripts/) and is importable.")
    # As a fallback, define ONS_INDICATORS_MAP if import fails, so script can be partially reviewed
    if 'ONS_INDICATORS_MAP' not in globals():
        ONS_INDICATORS_MAP = { # Default fallback, ensure this matches process_data.py
            "L55O": "CPIH", "D7G7": "CPI", "IHYQ": "GDP_Dataset", "MGSX": "Unemployment_Dataset"
        }
    # Exit if functions can't be imported, as the script cannot proceed
    if not all(func in globals() for func in ['load_and_process_fred_data', 'load_and_process_ons_data']):
        print("Critical functions from process_data.py could not be imported. Exiting.")
        exit(1)


# Define the directory to save charts (relative to this script's location)
CHARTS_DIR = os.path.join(SCRIPT_DIR, "..", "charts")

# Define indicator mappings for comparison
# Keys are generic names, values are the specific series IDs used in filenames/fetching
USD_INDICATOR_MAPPING = {
    'UNRATE': 'UNRATE',             # Unemployment Rate
    'CPI': 'CPIAUCSL',              # Consumer Price Index
    'GDP': 'GDP',                   # Gross Domestic Product
    'INTEREST_RATE': 'FEDFUNDS',    # Federal Funds Rate
    'PMI': 'NAPM'                   # Purchasing Managers' Index
}

# For GBP, we use the keys from ONS_INDICATORS_MAP (the values of that map are the 'indicator_name' part of filenames)
# The keys here should match the generic names in COMPARISON_TYPES
GBP_INDICATOR_MAPPING = {
    'UNRATE': 'Unemployment_Dataset', # Maps to MGSX via ONS_INDICATORS_MAP
    'CPI': 'CPIH',                  # Maps to L55O via ONS_INDICATORS_MAP (or D7G7 if preferred)
    'GDP': 'GDP_Dataset'            # Maps to IHYQ via ONS_INDICATORS_MAP
    # Interest Rate and PMI are not available from ONS script, so not mapped here
}
# We need to find the ONS series ID (e.g., L55O) from the descriptive name (e.g., CPIH)
# Invert ONS_INDICATORS_MAP for easy lookup: { 'CPIH': 'L55O', ... }
ONS_NAME_TO_ID_MAP = {v: k for k, v in ONS_INDICATORS_MAP.items()}


# Types of indicators to compare
COMPARISON_TYPES = ['UNRATE', 'CPI', 'GDP'] # Focus on these as they are more likely to exist for both

def main():
    # Create charts directory if it doesn't exist
    if not os.path.exists(CHARTS_DIR):
        try:
            os.makedirs(CHARTS_DIR)
            print(f"Created directory: {CHARTS_DIR}")
        except OSError as e:
            print(f"Error creating directory {CHARTS_DIR}: {e}")
            return # Exit if cannot create chart directory

    print(f"Generating comparison charts. Output will be in {CHARTS_DIR}")

    for indicator_theme in COMPARISON_TYPES:
        print(f"\nProcessing comparison for: {indicator_theme}")

        df_usd = pd.DataFrame() # Initialize as empty
        df_gbp = pd.DataFrame() # Initialize as empty

        # Fetch USD data
        usd_series_id = USD_INDICATOR_MAPPING.get(indicator_theme)
        if usd_series_id:
            # Data path is relative to process_data.py, which should handle it.
            # No need to pass data_dir if process_data.py's default is correct.
            df_usd = load_and_process_fred_data(usd_series_id)
            if df_usd.empty:
                print(f"  USD data for {indicator_theme} ({usd_series_id}) is empty or could not be loaded.")
            else:
                print(f"  Successfully loaded USD data for {indicator_theme} ({usd_series_id}).")
        else:
            print(f"  No USD mapping for {indicator_theme}.")

        # Fetch GBP data
        gbp_indicator_name = GBP_INDICATOR_MAPPING.get(indicator_theme) # e.g., 'CPIH'
        if gbp_indicator_name:
            gbp_ons_series_id = ONS_NAME_TO_ID_MAP.get(gbp_indicator_name) # e.g., 'L55O'
            if gbp_ons_series_id:
                # load_and_process_ons_data expects (ons_series_id, indicator_name)
                df_gbp = load_and_process_ons_data(gbp_ons_series_id, gbp_indicator_name)
                if df_gbp.empty:
                    print(f"  GBP data for {indicator_theme} ({gbp_indicator_name} - {gbp_ons_series_id}) is empty or could not be loaded.")
                else:
                    print(f"  Successfully loaded GBP data for {indicator_theme} ({gbp_indicator_name} - {gbp_ons_series_id}).")
            else:
                print(f"  Could not find ONS Series ID for GBP indicator name {gbp_indicator_name}.")
        else:
            print(f"  No GBP mapping for {indicator_theme}.")

        # Plotting if at least one DataFrame has data
        if not df_usd.empty or not df_gbp.empty:
            plt.figure(figsize=(12, 6))

            if not df_usd.empty and 'value' in df_usd.columns:
                plt.plot(df_usd.index, df_usd['value'], label=f"USD ({usd_series_id})", linestyle='-', marker='.')
            else:
                print(f"  Skipping plot for USD {indicator_theme} as data is empty or 'value' column missing.")

            if not df_gbp.empty and 'value' in df_gbp.columns:
                # If ONS data is monthly/quarterly, it might have fewer points or different frequency
                plt.plot(df_gbp.index, df_gbp['value'], label=f"GBP ({gbp_indicator_name})", linestyle='--', marker='x')
            else:
                print(f"  Skipping plot for GBP {indicator_theme} as data is empty or 'value' column missing.")

            plt.title(f"{indicator_theme} Comparison: USD vs GBP")
            plt.xlabel("Date")
            plt.ylabel("Value")
            plt.legend()
            plt.grid(True)
            plt.tight_layout()

            chart_filename = os.path.join(CHARTS_DIR, f"{indicator_theme}_USD_GBP_Comparison.png")
            try:
                plt.savefig(chart_filename)
                print(f"  Chart saved to {chart_filename}")
            except Exception as e:
                print(f"  Error saving chart {chart_filename}: {e}")

            plt.close() # Close the plot figure to free memory
        else:
            print(f"  No data available to plot for {indicator_theme}.")

    print("\nAll chart generation attempts complete.")

if __name__ == "__main__":
    # Pandas is used by the imported functions, ensure it's available
    try:
        import pandas as pd
    except ImportError:
        print("Pandas library is not installed. This script relies on functions from process_data.py which use Pandas.")
        print("Please install Pandas: pip install pandas")
        exit(1)

    main()
