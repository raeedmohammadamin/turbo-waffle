import requests
import json
import os

# FRED API Configuration
FRED_API_KEY = "ecb93fd3bf9e3e3a7ae60971f8628f72"
FRED_API_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"
SERIES_IDS = ["FEDFUNDS", "CPIAUCSL", "GDP", "UNRATE", "NAPM"]
DATA_DIR = "data/" # Should be ../data/ if script is run from scripts/ directory, or use absolute path

def fetch_fred_data(series_id, api_key, base_url):
    """
    Fetches economic data from the FRED API for a given series ID.

    Args:
        series_id (str): The FRED series ID (e.g., "FEDFUNDS").
        api_key (str): Your FRED API key.
        base_url (str): The base URL for the FRED API series/observations endpoint.

    Returns:
        dict: The JSON data for the series if successful, None otherwise.
    """
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
    }
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching data for {series_id}: Status Code {response.status_code}")
            print(f"Response text: {response.text}") # Print response text for more details
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {series_id}: Network exception {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for {series_id}: {e}")
        print(f"Response text was: {response.text}") # Show what was received
        return None


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    # Adjust DATA_DIR if running from a different location or use absolute paths
    # For this project structure, if running `python scripts/get_fred_data.py` from root:
    # DATA_DIR should be "data/"
    # If running `python get_fred_data.py` from `scripts/` directory:
    # DATA_DIR should be "../data/"

    # Assuming the script will be run from the root directory as `python scripts/get_fred_data.py`
    # Or if run from `scripts/`, `os.makedirs` needs to handle `../data`

    # Let's make DATA_DIR relative to the script's location for robustness
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir_path = os.path.join(script_dir, "..", "data") # Navigates to parent dir then to data/

    if not os.path.exists(data_dir_path):
        try:
            os.makedirs(data_dir_path)
            print(f"Created directory: {data_dir_path}")
        except OSError as e:
            print(f"Error creating directory {data_dir_path}: {e}")
            # Exit if directory creation fails, as we can't save data
            exit(1)
    else:
        print(f"Directory {data_dir_path} already exists.")

    print(f"Fetching data for Series IDs: {', '.join(SERIES_IDS)}")

    for series_id in SERIES_IDS:
        print(f"\nFetching data for {series_id}...")
        data = fetch_fred_data(series_id, FRED_API_KEY, FRED_API_BASE_URL)

        if data and "observations" in data: # Check if data is not None and has observations
            # Define filename, e.g., USD_FEDFUNDS.json
            filename = os.path.join(data_dir_path, f"USD_{series_id}.json")
            try:
                with open(filename, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"Successfully fetched and saved data for {series_id} to {filename}")
            except IOError as e:
                print(f"Error writing data to file {filename} for series {series_id}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while writing file for {series_id}: {e}")
        elif data: # Data fetched but might be an error JSON from FRED (e.g. API limit)
            print(f"Data fetched for {series_id}, but it might not contain 'observations'. Check API response.")
            # Optionally save this response too for debugging
            error_filename = os.path.join(data_dir_path, f"ERROR_USD_{series_id}.json")
            try:
                with open(error_filename, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"Saved error/unexpected response for {series_id} to {error_filename}")
            except IOError as e:
                print(f"Error writing error response to file {error_filename}: {e}")
        else:
            # fetch_fred_data already prints specific errors (network, status code)
            print(f"Failed to fetch data for {series_id}.")

    print("\nAll FRED data fetching attempts complete.")
