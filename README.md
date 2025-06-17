# turbo-waffle

## Data Sources

### US Dollar (USD)
*   **Provider:** Federal Reserve Economic Data (FRED)
*   **API Base URL:** `https://api.stlouisfed.org/fred/`
*   **API Key:** `ecb93fd3bf9e3e3a7ae60971f8628f72`
*   **Potential Series IDs:**
    *   Interest Rate (Federal Funds Rate): `FEDFUNDS`
    *   Inflation (CPI All Urban Consumers, Seasonally Adjusted): `CPIAUCSL`
    *   GDP (Gross Domestic Product, Billions of Dollars, Seasonally Adjusted Annual Rate): `GDP`
    *   Unemployment Rate (Seasonally Adjusted): `UNRATE`
    *   PMI (ISM Manufacturing Index - formally NAPM): `NAPM`

### British Pound (GBP)
*   **Provider:** Office for National Statistics (ONS)
*   **API Base URL:** `https://api.beta.ons.gov.uk/v1/`
*   **Potential Series IDs (Note: These require verification during script development as direct ONS documentation browsing is currently unavailable. Some indicators like Interest Rate and PMI might require alternative sourcing if direct ONS API endpoints are not found):**
    *   Interest Rate (Official Bank Rate): *To be confirmed (TBC) - ONS may not directly provide this; Bank of England is the primary source.*
    *   Inflation (Consumer Prices Index including owner occupiers’ housing costs (CPIH) % change over 12 months): `L55O`
    *   Inflation (Consumer Price Index (CPI) % change over 12 months): `D7G7`
    *   GDP (Gross Domestic Product: chained volume measures: Seasonally adjusted £m Y-on-Y % change): Series for dataset `IHYQ` to be identified.
    *   Unemployment Rate (UK seasonally adjusted rate for people aged 16+): Series for dataset `MGSX` to be identified.
    *   PMI (Purchasing Managers' Index): *TBC - ONS does not typically provide Markit/CIPS PMI data directly. This may need to be omitted or sourced manually.*

## Setup

To run this analysis, you need Python 3 and the following libraries:
*   requests
*   pandas
*   matplotlib
*   numpy

You can install these dependencies using pip:
```bash
pip install requests pandas matplotlib numpy
```

Ensure your FRED API key is correctly set in `scripts/get_fred_data.py` if you are modifying the script (currently it's hardcoded as per user provision).

## Running the Analysis

To execute the full analysis pipeline:
1.  Navigate to the root directory of the project in your terminal.
2.  Run the main script:
    ```bash
    python main.py
    ```
This will:
*   Fetch the latest economic data for USD (from FRED) and GBP (from ONS).
*   Process this data.
*   Generate comparison charts in the `charts/` directory.
*   Print a textual analysis of dovish/hawkish signals to the console.

## Interpreting Results

### Charts
The charts generated in the `charts/` directory provide visual comparisons of key economic indicators (e.g., Inflation, GDP, Unemployment Rate) between the US (USD) and the UK (GBP) over time. These help in understanding the relative economic performance trends.

### Dovish/Hawkish Signals
The console output from `main.py` (produced by `scripts/signal_logic.py`) provides a textual summary. For each currency (USD and GBP), it breaks down:
*   The latest available value for each economic indicator.
*   A simple trend assessment (e.g., "rising", "falling", "stable").
*   A "hawkish", "dovish", or "neutral" signal for that specific indicator.

**General Interpretation:**
*   **Hawkish:** Suggests a currency may strengthen. Associated with factors like higher or rising interest rates, strong economic growth, rising inflation (prompting potential rate hikes), low or falling unemployment, and strong PMI (>50).
*   **Dovish:** Suggests a currency may weaken. Associated with factors like lower or falling interest rates, weak economic growth, low inflation (or inflation falling below target), high or rising unemployment, and weak PMI (<50).

The script provides an "Overall" assessment for both USD and GBP, followed by a "Final Signal" indicating which currency is relatively more hawkish or dovish based on the aggregated analysis.

**Note on Data:** The analysis relies on the data availability and accuracy from the FRED and ONS APIs. Some indicators (like GBP Interest Rates and PMI) might be missing if not available from the specified ONS API endpoints and require manual checking or alternative sources for a complete picture.