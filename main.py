import subprocess
import sys
import os

# Determine the directory of this main.py script (should be the project root)
PROJECT_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Define the path to the scripts directory
SCRIPTS_DIR = os.path.join(PROJECT_ROOT_DIR, 'scripts')

def run_script(script_name, scripts_dir_path):
    """
    Executes a Python script using subprocess.run() and prints its output.

    Args:
        script_name (str): The name of the script to run (e.g., "get_fred_data.py").
        scripts_dir_path (str): The absolute path to the directory containing the scripts.

    Returns:
        bool: True if the script ran successfully, False otherwise.
    """
    full_script_path = os.path.join(scripts_dir_path, script_name)

    if not os.path.exists(full_script_path):
        print(f"Error: Script not found at {full_script_path}")
        return False

    print(f"Executing script: {full_script_path}...")
    try:
        # Using sys.executable ensures the script runs with the same Python interpreter
        process = subprocess.run(
            [sys.executable, full_script_path],
            check=True,          # Raises CalledProcessError for non-zero exit codes
            capture_output=True, # Captures stdout and stderr
            text=True            # Decodes stdout/stderr as text
        )
        print(f"--- Output from {script_name} ---")
        if process.stdout:
            print("Stdout:\n", process.stdout)
        if process.stderr: # Should be empty on success, but print if not
            print("Stderr:\n", process.stderr)
        print(f"--- End of {script_name} output ---")
        print(f"{script_name} executed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}:")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print("Stdout:\n", e.stdout)
        if e.stderr:
            print("Stderr:\n", e.stderr)
        return False
    except FileNotFoundError: # Should not happen if os.path.exists check passes, but good practice
        print(f"Error: The Python interpreter '{sys.executable}' or script '{full_script_path}' was not found.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while running {script_name}: {e}")
        return False

if __name__ == "__main__":
    print("Starting the economic data analysis pipeline...\n")

    # Define the sequence of scripts to be executed
    # process_data.py should run after data fetching and before visualization/signal logic
    scripts_to_run = [
        "get_fred_data.py",
        "get_ons_data.py",
        "process_data.py", # Processes the raw data fetched by the above scripts
        "visualize_data.py",
        "signal_logic.py"
    ]

    critical_data_scripts = ["get_fred_data.py", "get_ons_data.py", "process_data.py"]

    for script_file in scripts_to_run:
        print(f"--- Stage: {script_file} ---")
        success = run_script(script_file, SCRIPTS_DIR)
        if not success:
            print(f"Failed to execute {script_file}.")
            if script_file in critical_data_scripts:
                print(f"Critical script {script_file} failed. Halting pipeline.")
                break # Stop the pipeline if a critical data script fails
            else:
                print(f"Non-critical script {script_file} failed. Continuing pipeline with potentially incomplete data analysis or visualization.")
        if script_file == scripts_to_run[-1] and success:
             print(f"Successfully completed all stages of the analysis pipeline.")
        elif not success and script_file == scripts_to_run[-1]:
             print(f"Pipeline finished, but the last script {script_file} failed.")


    print("\nAnalysis pipeline execution attempt finished.")
