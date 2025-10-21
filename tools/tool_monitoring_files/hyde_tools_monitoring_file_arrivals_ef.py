import time
import os
import csv
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# List of folders to monitor, now directly including `{current_year}`
folders_to_watch = [
    f"/hydro/data/data_dynamic/source/subjective-forecast_aa2017/"
]

# Define the folder where log and csv folder will be saved
log_folder = "/hydro/log/service/"
csv_folder = "/hydro/monitoring/file_source/"

# Ensure the log folder exists
os.makedirs(log_folder, exist_ok=True)

# Configure logging
logging.basicConfig(filename=os.path.join(log_folder, "file_arrivals_ef.log"), level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Define the time threshold (last 10 days)
DAYS_AGO = time.time() - (10 * 24 * 60 * 60)

def is_recent(path):
    """Check if the folder or file was modified in the last 10 days."""
    return os.path.exists(path) and os.path.getmtime(path) >= DAYS_AGO

class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        # Check if the file is recent
        if not is_recent(event.src_path):
            return  # Ignore older files

        # Generate the CSV file path dynamically
        csv_file = os.path.join(csv_folder, f"file_arrivals_ef_{time.strftime('%Y-%m-%d')}.csv")

        # Extract folder path and file name
        file_folder = os.path.dirname(event.src_path)
        file_name = os.path.basename(event.src_path)

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

# Setting up watchdog observers for all folders
observers = []
for folder in folders_to_watch:
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, folder, recursive=True)
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

