import time
import os
import csv
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Get the current year dynamically
current_year = time.strftime("%Y")

# List of folders to monitor, now directly including `{current_year}`
folders_to_watch = [
    f"/hydro/data/data_dynamic/source/obs/river_stations/{current_year}/",
    f"/hydro/data/data_dynamic/source/obs/weather_stations/{current_year}/",
    f"/hydro/data/data_dynamic/source/obs/radar/{current_year}/",
    f"/hydro/data/data_dynamic/source/obs/dams/{current_year}/"
]

# Define the folder where log and csv folder will be saved
log_folder = "/hydro/log/service/"
csv_folder = "/hydro/monitoring/file_source/"

# Ensure the log folder exists
os.makedirs(log_folder, exist_ok=True)

# Configure logging
logging.basicConfig(filename=os.path.join(log_folder, "file_arrivals_obs.log"), level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Define the time threshold (last 10 days)
TEN_DAYS_AGO = time.time() - (10 * 24 * 60 * 60)

def is_recent(path):
    """Check if the folder or file was modified in the last 10 days."""
    return os.path.exists(path) and os.path.getmtime(path) >= TEN_DAYS_AGO

def is_line_present(csv_file, folder, filename):
    """Check if the file entry already exists in the CSV."""
    if not os.path.exists(csv_file):
        return False  # No file yet, so nothing to check

    with open(csv_file, "r", newline="") as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 3 and row[1] == folder and row[2] == filename:
                return True  # Entry already exists

    return False  # Not found, safe to add

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        # Check if the file is recent
        if not is_recent(event.src_path):
            return  # Ignore older files

        # Generate the CSV file path dynamically
        csv_file = os.path.join(csv_folder, f"file_arrivals_obs_{time.strftime('%Y-%m-%d')}.csv")

        # Extract folder path and file name
        file_folder = os.path.dirname(event.src_path)
        file_name = os.path.basename(event.src_path)

        # Check if the entry already exists in the CSV
        if is_line_present(csv_file, file_folder, file_name):
            logging.info(f"Duplicate file ignored: {file_name} in {file_folder}")
            return  # Skip writing

        try:
            # Write to CSV file (append mode) with `;` as delimiter
            with open(csv_file, "a", newline="") as f:
                writer = csv.writer(f, delimiter=';')

                # Ensure file has headers
                if not os.path.exists(csv_file) or os.stat(csv_file).st_size == 0:
                    writer.writerow(["Timestamp", "Folder", "Filename"])

                writer.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), file_folder, file_name])

            logging.info(f"New file detected: {file_name} in {file_folder} (logged in {csv_file})")

        except Exception as e:
            logging.error(f"Error writing to CSV: {e}")

# Setting up watchdog observers for **recent subfolders**
observers = []
for folder in folders_to_watch:
    if is_recent(folder):  # Ensure the main folder is recent
        for root, dirs, _ in os.walk(folder):  # Walk through subfolders
            for subfolder in dirs:
                subfolder_path = os.path.join(root, subfolder)
                if is_recent(subfolder_path):  # Check if subfolder is recent
                    event_handler = MyHandler()
                    observer = Observer()
                    observer.schedule(event_handler, subfolder_path, recursive=True)
                    observer.start()
                    observers.append(observer)

try:
    logging.info("Monitoring started...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    for observer in observers:
        observer.stop()
    for observer in observers:
        observer.join()
    logging.info("Monitoring stopped.")

