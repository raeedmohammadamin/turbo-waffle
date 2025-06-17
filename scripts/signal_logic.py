import pandas as pd
import numpy as np # For NaN comparison if necessary
import sys
import os
from datetime import datetime

# Add the script's directory to sys.path to allow importing process_data
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

try:
    from process_data import load_and_process_fred_data, load_and_process_ons_data, ONS_INDICATORS_MAP, USD_INDICATORS
except ImportError as e:
    print(f"Error importing from process_data: {e}")
    print("Ensure process_data.py is in the same directory (scripts/) and is importable.")
    # Define fallbacks if import fails for partial review
    if 'ONS_INDICATORS_MAP' not in globals():
        ONS_INDICATORS_MAP = {"L55O": "CPIH", "D7G7": "CPI", "IHYQ": "GDP_Dataset", "MGSX": "Unemployment_Dataset"}
    if 'USD_INDICATORS' not in globals():
        USD_INDICATORS = ["FEDFUNDS", "CPIAUCSL", "GDP", "UNRATE", "NAPM"]
    if not all(func in globals() for func in ['load_and_process_fred_data', 'load_and_process_ons_data']):
        print("Critical functions from process_data.py could not be imported. Exiting.")
        exit(1)

# Helper to invert ONS_INDICATORS_MAP for lookups if needed
ONS_NAME_TO_ID_MAP = {v: k for k, v in ONS_INDICATORS_MAP.items()}


def get_latest_data(data_frame):
    """
    Takes a processed Pandas DataFrame and returns the latest available value and its date.
    """
    if data_frame is None or data_frame.empty or 'value' not in data_frame.columns:
        return None, None
    latest_entry = data_frame['value'].dropna().iloc[-1:]
    if latest_entry.empty:
        return None, None
    return latest_entry.values[0], latest_entry.index[0]

def get_simple_trend(data_frame, periods=3, data_label=""):
    """
    Calculates a simple trend based on the change over a number of recent periods.
    Returns a qualitative trend (e.g., "rising", "falling", "stable") or numerical change.
    """
    if data_frame is None or data_frame.empty or 'value' not in data_frame.columns or len(data_frame['value'].dropna()) < periods:
        # print(f"Trend for {data_label}: Insufficient data (need {periods}, have {len(data_frame['value'].dropna()) if data_frame is not None else 0}).")
        return "insufficient data"

    recent_values = data_frame['value'].dropna().tail(periods)
    if len(recent_values) < 2: # Need at least two points to determine a trend
        # print(f"Trend for {data_label}: Insufficient recent values (need at least 2, have {len(recent_values)}).")
        return "insufficient data"

    # Simple difference: current vs value N periods ago
    # More robust: consider average of first few vs average of last few, or linear regression slope
    change = recent_values.iloc[-1] - recent_values.iloc[0]

    # Define thresholds for "stable" - this is subjective
    # Example: change less than 0.5% of the value, or a small absolute change for rates/indices
    # For simplicity, let's use a small absolute threshold for now.
    # This will need tuning based on indicator type.
    # For rates/percentages, 0.1 might be significant. For GDP, much larger.
    # For now, a generic approach:
    threshold_multiplier = 0.01 # 1% change relative to the first value
    stable_threshold = abs(recent_values.iloc[0] * threshold_multiplier) if recent_values.iloc[0] != 0 else 0.05

    if abs(change) < stable_threshold:
        return "stable"
    elif change > 0:
        return "rising"
    else:
        return "falling"

def determine_dovish_hawkish_signals():
    """
    Main analysis function to determine dovish/hawkish signals for USD and GBP.
    """
    # --- Indicator Mappings ---
    # Using descriptive keys for clarity in the report
    usd_fred_series_map = {
        'Interest Rate': 'FEDFUNDS',
        'Inflation': 'CPIAUCSL', # CPI All Urban Consumers, Seasonally Adjusted
        'GDP': 'GDP',            # Gross Domestic Product, Billions of Dollars, SAAR
        'Unemployment': 'UNRATE',# Unemployment Rate, Seasonally Adjusted
        'PMI': 'NAPM'            # ISM Manufacturing Index (PMI)
    }
    # ONS: map descriptive key to the 'indicator_name' used in process_data.py (which then maps to ONS ID)
    gbp_ons_name_map = {
        'Inflation': 'CPIH',    # Consumer Prices Index including owner occupiers’ housing costs (CPIH)
        'GDP': 'GDP_Dataset',   # Gross Domestic Product: chained volume measures dataset
        'Unemployment': 'Unemployment_Dataset' # Unemployment rate UK dataset
        # Note: Interest Rate (Bank of England) and PMI are not sourced from ONS by current scripts.
    }

    # --- Data Loading ---
    print("Loading and processing data for signal logic...")
    usd_data = {}
    for desc_name, fred_id in usd_fred_series_map.items():
        usd_data[desc_name] = load_and_process_fred_data(fred_id)
        # print(f"Loaded USD {desc_name} (FRED: {fred_id}), DataFrame empty: {usd_data[desc_name].empty}")


    gbp_data = {}
    for desc_name, ons_name in gbp_ons_name_map.items():
        ons_id = ONS_NAME_TO_ID_MAP.get(ons_name) # Get 'L55O' from 'CPIH'
        if ons_id:
            gbp_data[desc_name] = load_and_process_ons_data(ons_id, ons_name)
            # print(f"Loaded GBP {desc_name} (ONS_ID: {ons_id}, Name: {ons_name}), DataFrame empty: {gbp_data[desc_name].empty}")
        else:
            gbp_data[desc_name] = pd.DataFrame() # Ensure key exists
            # print(f"GBP Indicator {desc_name} (ONS Name: {ons_name}) - ONS ID not found in map.")

    # Add placeholders for missing GBP indicators to simplify report structure
    if 'Interest Rate' not in gbp_data: gbp_data['Interest Rate'] = pd.DataFrame()
    if 'PMI' not in gbp_data: gbp_data['PMI'] = pd.DataFrame()


    # --- Signal Generation ---
    usd_signals = {} # Store detailed signal string for each indicator
    gbp_signals = {}
    usd_hawkish_score = 0
    gbp_hawkish_score = 0

    report_lines = []

    # Iterate through a common set of indicator types for structured comparison
    indicator_types = ['Interest Rate', 'Inflation', 'GDP', 'Unemployment', 'PMI']

    for ind_type in indicator_types:
        # --- USD Analysis ---
        df_usd = usd_data.get(ind_type)
        usd_latest_val, usd_latest_date = get_latest_data(df_usd)
        usd_trend = get_simple_trend(df_usd, data_label=f"USD {ind_type}")
        usd_signal_qual = "neutral"

        usd_val_str = f"{usd_latest_val:.2f}%" if usd_latest_val is not None and ind_type in ['Interest Rate', 'Inflation', 'Unemployment'] else \
                      f"${usd_latest_val:,.0f}B" if usd_latest_val is not None and ind_type == 'GDP' else \
                      f"{usd_latest_val:.1f}" if usd_latest_val is not None and ind_type == 'PMI' else "N/A"
        usd_date_str = usd_latest_date.strftime('%Y-%m-%d') if usd_latest_date else "N/A"

        # USD Signal Logic (Simplified)
        if ind_type == 'Interest Rate' and usd_latest_val is not None:
            if usd_latest_val > 2.5: usd_signal_qual = "hawkish"; usd_hawkish_score +=1 # Arbitrary threshold
            if usd_trend == "rising": usd_signal_qual = "hawkish"; usd_hawkish_score +=1
            elif usd_trend == "falling": usd_signal_qual = "dovish"; usd_hawkish_score -=1
        elif ind_type == 'Inflation' and usd_latest_val is not None:
            if usd_latest_val > 2.0: usd_signal_qual = "hawkish"; usd_hawkish_score +=1 # Target inflation
            if usd_trend == "rising": usd_signal_qual = "hawkish"; usd_hawkish_score +=1
            elif usd_trend == "falling": usd_signal_qual = "dovish"; usd_hawkish_score -=1
        elif ind_type == 'GDP' and usd_latest_val is not None: # Here, trend (growth rate) is more important than level
            # Assume 'value' for GDP is growth rate YoY or QoQ. If it's absolute level, trend is key.
            # For this example, let's assume the 'value' is level, so trend is primary.
            if usd_trend == "rising": usd_signal_qual = "hawkish"; usd_hawkish_score +=1 # Strong growth
            elif usd_trend == "falling": usd_signal_qual = "dovish"; usd_hawkish_score -=1 # Weakening growth
        elif ind_type == 'Unemployment' and usd_latest_val is not None:
            if usd_latest_val < 4.5: usd_signal_qual = "hawkish"; usd_hawkish_score +=1 # Low unemployment
            if usd_trend == "falling": usd_signal_qual = "hawkish"; usd_hawkish_score +=1
            elif usd_trend == "rising": usd_signal_qual = "dovish"; usd_hawkish_score -=1
        elif ind_type == 'PMI' and usd_latest_val is not None:
            if usd_latest_val > 50: usd_signal_qual = "hawkish"; usd_hawkish_score +=1 # Expansion
            if usd_trend == "rising": usd_signal_qual = "hawkish"; usd_hawkish_score +=0.5 # PMI trend less impactful than level
            elif usd_trend == "falling" and usd_latest_val < 50 : usd_signal_qual = "dovish"; usd_hawkish_score -=1 # Contraction and falling

        usd_signals[ind_type] = f"{usd_fred_series_map.get(ind_type, 'N/A')}: {usd_val_str} (Latest: {usd_date_str}) - Trend: {usd_trend} - Signal: {usd_signal_qual.capitalize()}"

        # --- GBP Analysis ---
        df_gbp = gbp_data.get(ind_type)
        gbp_latest_val, gbp_latest_date = get_latest_data(df_gbp)
        gbp_trend = get_simple_trend(df_gbp, data_label=f"GBP {ind_type}")
        gbp_signal_qual = "neutral"

        gbp_val_str = f"{gbp_latest_val:.2f}%" if gbp_latest_val is not None and ind_type in ['Interest Rate', 'Inflation', 'Unemployment'] else \
                      f"£{gbp_latest_val:,.0f}B" if gbp_latest_val is not None and ind_type == 'GDP' else \
                      f"{gbp_latest_val:.1f}" if gbp_latest_val is not None and ind_type == 'PMI' else "N/A"
        gbp_date_str = gbp_latest_date.strftime('%Y-%m-%d') if gbp_latest_date else "N/A"

        # GBP Signal Logic (Simplified) - Similar to USD for brevity
        # (In reality, thresholds might differ based on central bank targets, economic context)
        if ind_type == 'Interest Rate' and gbp_latest_val is not None: # Not available from ONS script
            if gbp_latest_val > 2.5: gbp_signal_qual = "hawkish"; gbp_hawkish_score +=1
            if gbp_trend == "rising": gbp_signal_qual = "hawkish"; gbp_hawkish_score +=1
            elif gbp_trend == "falling": gbp_signal_qual = "dovish"; gbp_hawkish_score -=1
        elif ind_type == 'Inflation' and gbp_latest_val is not None:
            if gbp_latest_val > 2.0: gbp_signal_qual = "hawkish"; gbp_hawkish_score +=1
            if gbp_trend == "rising": gbp_signal_qual = "hawkish"; gbp_hawkish_score +=1
            elif gbp_trend == "falling": gbp_signal_qual = "dovish"; gbp_hawkish_score -=1
        elif ind_type == 'GDP' and gbp_latest_val is not None:
            if gbp_trend == "rising": gbp_signal_qual = "hawkish"; gbp_hawkish_score +=1
            elif gbp_trend == "falling": gbp_signal_qual = "dovish"; gbp_hawkish_score -=1
        elif ind_type == 'Unemployment' and gbp_latest_val is not None:
            if gbp_latest_val < 4.5: gbp_signal_qual = "hawkish"; gbp_hawkish_score +=1
            if gbp_trend == "falling": gbp_signal_qual = "hawkish"; gbp_hawkish_score +=1
            elif gbp_trend == "rising": gbp_signal_qual = "dovish"; gbp_hawkish_score -=1
        elif ind_type == 'PMI' and gbp_latest_val is not None: # Not available from ONS script
            if gbp_latest_val > 50: gbp_signal_qual = "hawkish"; gbp_hawkish_score +=1
            if gbp_trend == "rising": gbp_signal_qual = "hawkish"; gbp_hawkish_score +=0.5
            elif gbp_trend == "falling" and gbp_latest_val < 50 : gbp_signal_qual = "dovish"; gbp_hawkish_score -=1

        gbp_series_name_for_report = gbp_ons_name_map.get(ind_type, 'N/A')
        # Find ONS ID if available for reporting:
        ons_id_for_report = ONS_NAME_TO_ID_MAP.get(gbp_series_name_for_report, "")
        gbp_full_series_id_str = f"{gbp_series_name_for_report} ({ons_id_for_report})" if ons_id_for_report else gbp_series_name_for_report

        gbp_signals[ind_type] = f"{gbp_full_series_id_str}: {gbp_val_str} (Latest: {gbp_date_str}) - Trend: {gbp_trend} - Signal: {gbp_signal_qual.capitalize()}"


    # --- Aggregation and Summary ---
    report_lines.append("USD Analysis:")
    for ind_type in indicator_types:
        report_lines.append(f"- {ind_type} ({usd_signals.get(ind_type, 'Data N/A')})")

    overall_usd_stance = "Neutral"
    if usd_hawkish_score > 1: overall_usd_stance = "Hawkish"
    elif usd_hawkish_score < -1: overall_usd_stance = "Dovish"
    report_lines.append(f"Overall USD: {overall_usd_stance} (Score: {usd_hawkish_score:.1f})\n")

    report_lines.append("GBP Analysis:")
    for ind_type in indicator_types:
        # Handle cases where GBP indicator might be entirely missing from gbp_ons_name_map
        gbp_signal_line = gbp_signals.get(ind_type)
        if not gbp_signal_line : # If ind_type (e.g. 'Interest Rate') wasn't in gbp_ons_name_map
             report_lines.append(f"- {ind_type} (Data N/A - Not configured for GBP ONS collection)")
        else:
             report_lines.append(f"- {ind_type} ({gbp_signal_line})")


    overall_gbp_stance = "Neutral"
    if gbp_hawkish_score > 1: overall_gbp_stance = "Hawkish"
    elif gbp_hawkish_score < -1: overall_gbp_stance = "Dovish"
    report_lines.append(f"Overall GBP: {overall_gbp_stance} (Score: {gbp_hawkish_score:.1f})\n")

    final_comparison = "Relative stance: "
    if usd_hawkish_score > gbp_hawkish_score + 1: # Threshold for significant difference
        final_comparison += "USD More Hawkish / GBP More Dovish"
    elif gbp_hawkish_score > usd_hawkish_score + 1:
        final_comparison += "GBP More Hawkish / USD More Dovish"
    else:
        final_comparison += "Broadly Similar Stance"
        if overall_usd_stance == overall_gbp_stance:
            final_comparison += f" (Both {overall_usd_stance})"

    report_lines.append(final_comparison)

    return "\n".join(report_lines)

if __name__ == "__main__":
    print("Starting Dovish/Hawkish Signal Analysis...")
    summary_report = determine_dovish_hawkish_signals()
    print("\n--- Signal Report ---")
    print(summary_report)
    print("--- End of Report ---")
