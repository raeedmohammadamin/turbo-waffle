import requests
import json
import os

# ONS API Configuration
ONS_API_BASE_URL = "https://api.beta.ons.gov.uk/v1/"

# Dictionary of indicators and their ONS series IDs or dataset identifiers
# Note: Interest Rates (Bank of England Official Bank Rate) and PMI data are not expected
# to be retrieved by this script and will need separate handling or manual input if required.
ONS_IDENTIFIERS = {
    "CPIH": {"id": "L55O", "is_dataset": False},  # Consumer Prices Index including owner occupiers’ housing costs (CPIH)
    "CPI": {"id": "D7G7", "is_dataset": False},   # Consumer Price Index (CPI)
    # For datasets, the API endpoint and data structure might be more complex.
    # This script will attempt a basic fetch, but it might only get general dataset info
    # or require more specific parameters (e.g., edition, version) for actual observations.
    "GDP_Dataset": {"id": "IHYQ", "is_dataset": True}, # Gross Domestic Product: chained volume measures
    "Unemployment_Dataset": {"id": "MGSX", "is_dataset": True} # Unemployment rate UK
}

# DATA_DIR should be relative to the script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR_PATH = os.path.join(SCRIPT_DIR, "..", "data")

def fetch_ons_data(identifier, base_url, is_dataset=False):
    """
    Fetches data from the ONS API for a given series or dataset identifier.

    Args:
        identifier (str): The ONS series ID or dataset ID.
        base_url (str): The base URL for the ONS API.
        is_dataset (bool): True if the identifier is for a dataset, False for a timeseries.

    Returns:
        dict: The JSON data if successful, None otherwise.
    """
    if is_dataset:
        # Constructing URL for dataset observations.
        # This is a potential endpoint. ONS API might require more specific details (editions/versions)
        # or have a different structure for fetching all observations of a dataset.
        # Refer to ONS API documentation for precise dataset observation retrieval.
        url = f"{base_url}datasets/{identifier}/observations"
        # An alternative might be to list editions and versions first, then get specific data.
        # e.g., /datasets/{id}/editions/{edition}/versions/{version}/observations
        print(f"Note: Fetching from dataset ID {identifier}. Endpoint used: {url}. This may require specific version/edition parameters not handled by this basic script.")
    else:
        url = f"{base_url}timeseries/{identifier}/data"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching data for {identifier}: Status Code {response.status_code}")
            print(f"URL attempted: {url}")
            print(f"Response text: {response.text}") # Print response text for more details
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {identifier}: Network exception {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for {identifier}: {e}")
        print(f"Response text was: {response.text if 'response' in locals() else 'Response object not created'}")
        return None

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    if not os.path.exists(DATA_DIR_PATH):
        try:
            os.makedirs(DATA_DIR_PATH)
            print(f"Created directory: {DATA_DIR_PATH}")
        except OSError as e:
            print(f"Error creating directory {DATA_DIR_PATH}: {e}")
            exit(1) # Exit if directory creation fails
    else:
        print(f"Directory {DATA_DIR_PATH} already exists.")

    print("\nFetching data from ONS API...")
    print("Note: Bank of England Official Bank Rate and PMI data are not retrieved by this script.")

    for indicator_name, info in ONS_IDENTIFIERS.items():
        series_id = info["id"]
        is_dataset = info["is_dataset"]

        print(f"\nFetching data for {indicator_name} ({series_id})...")
        data = fetch_ons_data(series_id, ONS_API_BASE_URL, is_dataset)

        if data:
            # Define filename, e.g., GBP_CPIH.json
            filename = os.path.join(DATA_DIR_PATH, f"GBP_{indicator_name}.json")
            try:
                with open(filename, "w") as f:
                    json.dump(data, f, indent=4)
                print(f"Successfully fetched and saved data for {indicator_name} to {filename}")
            except IOError as e:
                print(f"Error writing data to file {filename} for indicator {indicator_name}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while writing file for {indicator_name}: {e}")

            if is_dataset:
                print(f"Note: For dataset '{indicator_name}', the saved file contains the response from the dataset endpoint. This might be a list of available versions/editions or general dataset metadata. Further processing or more specific API calls might be needed to get detailed time series observations from datasets.")
                if not data.get("observations") and isinstance(data, dict) and data.get("links"):
                     print(f"The response for dataset {indicator_name} does not seem to contain direct observations. It might contain links to specific versions or editions. Check the content of {filename}.")

        else:
            # fetch_ons_data already prints specific errors
            print(f"Failed to fetch data for {indicator_name} ({series_id}).")

    print("\nAll ONS data fetching attempts complete.")
