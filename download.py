#!/usr/bin/python3

import os
import glob
import shutil
import datetime
import subprocess
import requests
import json
import sys
import time

# --- Configuration ---
LOG_FILE = "/home/osmc/scripts/download.log"
SOURCE_MEDIA_DIR = "/media/"
DESTINATION_BASE_DIR = "/mnt/unifi/Unsorted_Videos/"
VALID_VIDEO_EXTENSIONS = [".mp4", ".mov"] # Lowercase with `.`
KODI_RPC_URL = "http://localhost:80/jsonrpc"
KODI_NOTIFICATION_DISPLAY_TIME_MS = 7000 # 7 seconds

# --- Logging Function ---
def log_message(message: str, level: str = "INFO"):
    """Appends a timestamped message to the script's log file."""
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{current_time}] [{level}] {message}\n"
    with open(LOG_FILE, "a") as log:
        log.write(log_entry)
    print(f"[{level}] {message}") # Also print to console for immediate feedback

# --- Kodi Notification Function ---
def send_kodi_notification(title: str, message: str, displaytime_ms: int = KODI_NOTIFICATION_DISPLAY_TIME_MS, image_type: str = "info") -> bool:
    """
    Sends an on-screen notification to Kodi via its JSON-RPC API.

    Args:
        title (str): The title of the notification.
        message (str): The main message content of the notification.
        displaytime_ms (int): How long the notification should be displayed in milliseconds.
                               Default is 7000ms (7 seconds).
        image_type (str): The type of image/icon to display with the notification.
                          Common built-in Kodi icons include "info", "warning", "error".
                          You can also specify a path to a custom image file if accessible by Kodi.

    Returns:
        bool: True if the notification was sent successfully, False otherwise.
    """
    log_message(f"Attempting to send Kodi notification: Title='{title}', Message='{message}'", level="DEBUG")
    headers = {'Content-Type': 'application/json'}

    payload = {
        "jsonrpc": "2.0",
        "method": "GUI.ShowNotification",
        "params": {
            "title": title,
            "message": message,
            "displaytime": displaytime_ms,
            "image": image_type
        },
        "id": 1
    }

    try:
        response = requests.post(KODI_RPC_URL, headers=headers, data=json.dumps(payload), timeout=5)
        response.raise_for_status()

        result = response.json()

        if 'error' in result:
            error_message = result['error']['message']
            log_message(f"Error from Kodi API: {error_message}", level="ERROR")
            return False
        else:
            log_message("Kodi notification sent successfully.", level="DEBUG")
            return True

    except requests.exceptions.ConnectionError:
        log_message("Error: Could not connect to Kodi. Please ensure Kodi is running and its web server/JSON-RPC is enabled (Settings -> Services -> Control).", level="ERROR")
        return False
    except requests.exceptions.Timeout:
        log_message("Error: Request to Kodi timed out. Kodi might be busy or unreachable.", level="ERROR")
        return False
    except requests.exceptions.RequestException as e:
        log_message(f"An unexpected error occurred while sending the request to Kodi: {e}", level="ERROR")
        return False
    except json.JSONDecodeError:
        log_message(f"Error: Could not decode JSON response from Kodi. Response: {response.text}", level="ERROR")
        return False
    except Exception as e:
        log_message(f"An unforeseen error occurred during Kodi notification: {e}", level="ERROR")
        return False

# --- File System Utility Functions ---
def clean_filename(filepath: str) -> str:
    """
    Cleans up a filename by removing '._' prefixes and leading/trailing single quotes.
    This is often necessary for files copied from HFS+ formatted SD cards.
    Returns the new path if renamed, otherwise the original path.
    """
    directory, filename = os.path.split(filepath)
    cleaned_filename = filename

    # Remove '._' prefix
    if cleaned_filename.startswith('._'):
        cleaned_filename = cleaned_filename[2:]
        log_message(f"Removed '._' prefix from '{filename}'. New name: '{cleaned_filename}'", level="DEBUG")

    # Remove leading and trailing single quotes
    if cleaned_filename.startswith("'") and cleaned_filename.endswith("'"):
        cleaned_filename = cleaned_filename.strip("'")
        log_message(f"Removed leading/trailing quotes from '{filename}'. New name: '{cleaned_filename}'", level="DEBUG")
    elif cleaned_filename.startswith("'"):
        cleaned_filename = cleaned_filename.lstrip("'")
        log_message(f"Removed leading quote from '{filename}'. New name: '{cleaned_filename}'", level="DEBUG")
    elif cleaned_filename.endswith("'"):
        cleaned_filename = cleaned_filename.rstrip("'")
        log_message(f"Removed trailing quote from '{filename}'. New name: '{cleaned_filename}'", level="DEBUG")

    if cleaned_filename != filename:
        new_filepath = os.path.join(directory, cleaned_filename)
        try:
            os.rename(filepath, new_filepath)
            log_message(f"Renamed '{filepath}' to '{new_filepath}'.", level="INFO")
            return new_filepath
        except OSError as e:
            log_message(f"Error renaming file from '{filepath}' to '{new_filepath}': {e}", level="ERROR")
            return filepath # Return original path if rename fails
    return filepath # No change needed

def get_latest_video_files(root_dir, count=3):
    """
    Finds the 'count' latest video files (based on VALID_VIDEO_EXTENSIONS)
    in any subdirectory of root_dir.
    """
    log_message(f"Scanning '{root_dir}' for the latest {count} video files.", level="INFO")
    file_list = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            fileExt = os.path.splitext(file)[1]
            if fileExt.lower() in VALID_VIDEO_EXTENSIONS:
                file_path = os.path.join(root, file)
                try:
                    modified_time = os.path.getmtime(file_path)
                    file_list.append((file_path, modified_time))
                except OSError as e:
                    log_message(f"Could not get modification time for '{file_path}': {e}", level="WARNING")
                    continue

    if not file_list:
        log_message(f"No video files ({', '.join(VALID_VIDEO_EXTENSIONS)}) found in '{root_dir}'.", level="INFO")
        return []

    file_list.sort(key=lambda item: item[1], reverse=True)
    latest_files = [item[0] for item in file_list[:count]]
    log_message(f"Found {len(latest_files)} latest video files in '{root_dir}'.", level="INFO")
    return latest_files

def get_most_recent_removable_media(media_root_dir):
    """
    Identifies the most recently added removable storage in the specified media root directory.
    Assumes removable media are subdirectories within media_root_dir.
    """
    log_message(f"Searching for most recent removable media in '{media_root_dir}'.", level="INFO")
    try:
        subdirectories = [os.path.join(media_root_dir, d) for d in os.listdir(media_root_dir) if os.path.isdir(os.path.join(media_root_dir, d))]
        if not subdirectories:
            log_message(f"No subdirectories found in '{media_root_dir}'. No removable media detected.", level="WARNING")
            return None

        # Sort subdirectories by their modification time (most recent first)
        subdirectories.sort(key=os.path.getmtime, reverse=True)

        most_recent_media_path = subdirectories[0]
        media_name = os.path.basename(most_recent_media_path)
        log_message(f"Most recently detected removable media: '{media_name}' at '{most_recent_media_path}'.", level="INFO")
        return media_name
    except FileNotFoundError:
        log_message(f"Error: Source directory '{media_root_dir}' not found. Cannot check for removable media.", level="ERROR")
        send_kodi_notification("Media Scan Failed", f"Source directory '{media_root_dir}' not found.", image_type="error")
        return None
    except Exception as e:
        log_message(f"An error occurred while finding removable media in '{media_root_dir}': {e}", level="ERROR")
        send_kodi_notification("Media Scan Failed", f"Error detecting media: {e}", image_type="error")
        return None

def find_file_in_destination(original_file_name, destination_sd_card_dir):
    """
    Checks if a file with the original name (plus optional date and counter)
    exists within the specified SD card's destination directory.
    This function has been modified to account for the new naming convention
    and wildcard matching.
    """
    log_message(f"Checking if '{original_file_name}' (or dated/numbered versions) already exists in '{destination_sd_card_dir}'...", level="DEBUG")
    
    base_name, ext = os.path.splitext(original_file_name)
    
    # Check for the exact original file name with appended date (e.g., "MyVideo - 2023-10-27.mp4")
    # This assumes the current date for the check, which aligns with how the files are named on copy.
    current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    expected_dated_name = f"{base_name} - {current_date_str}{ext}"
    if os.path.exists(os.path.join(destination_sd_card_dir, expected_dated_name)):
        log_message(f"Found existing file: '{expected_dated_name}'.", level="DEBUG")
        return True

    # Check for original name with appended date and counter (e.g., "MyVideo - 2023-10-27 - 1.mp4")
    # Using glob to find any file matching the pattern
    wildcard_pattern = f"{base_name} - {current_date_str} -*{ext}"
    if glob.glob(os.path.join(destination_sd_card_dir, wildcard_pattern)):
        log_message(f"Found existing file matching wildcard pattern: '{wildcard_pattern}'.", level="DEBUG")
        return True

    log_message(f"'{original_file_name}' (or dated/numbered versions) not found in '{destination_sd_card_dir}'.", level="DEBUG")
    return False


def check_and_copy_files(source_files, base_destination_path, media_identifier: str):
    """
    Checks if source files exist anywhere within the base_destination_path (including subdirectories).
    If a file does not exist, it's added to a list for copying.
    Files are copied into a folder named after the SD card.
    During transfer, files are renamed with a date and an incrementing number for duplicates on the same date.
    After copying, files are cleaned using the `clean_filename` function.
    """
    log_message(f"Initiating check and copy process for {len(source_files)} files to '{base_destination_path}'.", level="INFO")
    send_kodi_notification("Video Transfer", "Starting video transfer process...", image_type="info")

    destination_dir = os.path.join(base_destination_path, media_identifier)

    # Create the destination directory if it doesn't exist
    if not os.path.exists(destination_dir):
        log_message(f"Creating destination directory for SD card: '{destination_dir}'.", level="INFO")
        try:
            os.makedirs(destination_dir, exist_ok=True)
        except OSError as e:
            log_message(f"Error creating destination directory '{destination_dir}': {e}", level="ERROR")
            send_kodi_notification("Transfer Failed", f"Failed to create destination folder for '{media_identifier}'", image_type="error")
            return
    else:
        log_message(f"Destination directory for SD card already exists: '{destination_dir}'. Adding new files.", level="INFO")

    files_to_copy = []
    skipped_count = 0

    for source_file in source_files:
        file_name = os.path.basename(source_file)
        if not find_file_in_destination(file_name, destination_dir): # Check if the original file name exists anywhere in the SD card's destination folder
            files_to_copy.append(source_file)
            log_message(f"'{file_name}' is new and will be copied.", level="INFO")
        else:
            log_message(f"Skipped: Original file '{file_name}' (or a dated/numbered version) already exists in '{destination_dir}'.", level="INFO")
            skipped_count += 1

    if not files_to_copy:
        log_message("No new videos detected for copying. All checked videos already exist in the destination.", level="INFO")
        send_kodi_notification("Video Transfer Complete", "No new videos to download. All checked videos already exist.", image_type="info")
        return

    send_kodi_notification("Video Transfer", f"Preparing to transfer {len(files_to_copy)} new videos...", image_type="info")

    copied_count = 0
    total_files_to_copy = len(files_to_copy)
    current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    for i, source_file in enumerate(files_to_copy):
        original_file_name, file_extension = os.path.splitext(os.path.basename(source_file))

        # Start with base name + date
        new_file_name_base = f"{original_file_name} - {current_date_str}"
        
        # Check for conflicts for the current date and add incrementing number if needed
        counter = 0
        final_file_name = f"{new_file_name_base}{file_extension}"
        while os.path.exists(os.path.join(destination_dir, final_file_name)):
            counter += 1
            final_file_name = f"{new_file_name_base} - {counter}{file_extension}"

        destination_file_path = os.path.join(destination_dir, final_file_name)

        log_message(f"Copying '{os.path.basename(source_file)}' as '{final_file_name}' ({i + 1}/{total_files_to_copy})...", level="INFO")
        try:
            # Use 'sudo' for copying to ensure permissions if necessary
            subprocess.run(['sudo', 'cp', source_file, destination_file_path], check=True, capture_output=True, text=True)
            copied_count += 1
            log_message(f"Successfully copied: '{source_file}' to '{destination_file_path}'", level="INFO")
            send_kodi_notification("Video Transfer Progress", f"Copied {copied_count} of {total_files_to_copy} videos. '{final_file_name}'", image_type="info")
            
            # Clean the filename after successful copy
            clean_filename(destination_file_path)
            
            time.sleep(0.5) # Small delay to allow notification to show

        except subprocess.CalledProcessError as e:
            log_message(f"Error copying '{source_file}': {e.stderr.strip() if e.stderr else e}", level="ERROR")
            send_kodi_notification("File Transfer Failed", f"Failed to copy: '{final_file_name}'", image_type="error")
        except Exception as e:
            log_message(f"An unexpected error occurred while copying '{source_file}': {e}", level="ERROR")
            send_kodi_notification("File Transfer Failed", f"Unexpected error copying: '{final_file_name}'", image_type="error")

    if copied_count > 0:
        log_message(f"Successfully copied {copied_count} new videos to '{media_identifier}'. Total skipped: {skipped_count}", level="INFO")
        send_kodi_notification("Video Transfer Complete", f"Successfully copied {copied_count} new videos to '{media_identifier}'.", image_type="info")
    else:
        log_message(f"No new videos were copied. All {total_files_to_copy} files either existed or failed to copy.", level="WARNING")
        send_kodi_notification("Video Transfer", "No new videos were copied.", image_type="warning")

# --- Main Execution ---
if __name__ == "__main__":
    log_message("Script started: Initiating video transfer process.", level="INFO")
    send_kodi_notification("Video Transfer Script", "Script initiated. Checking for new videos...", image_type="info")

    most_recent_media_name = get_most_recent_removable_media(SOURCE_MEDIA_DIR)

    if most_recent_media_name:
        log_message(f"Identified '{most_recent_media_name}' as the most recently added removable media.", level="INFO")
        full_source_path = os.path.join(SOURCE_MEDIA_DIR, most_recent_media_name)
        send_kodi_notification("Media Detected", f"Found removable media: '{most_recent_media_name}'. Scanning for videos...", image_type="info")

        # Get the latest files from the removable media
        latest_files_on_removable_media = get_latest_video_files(full_source_path)

        if latest_files_on_removable_media:
            log_message(f"Found {len(latest_files_on_removable_media)} potential video files on '{most_recent_media_name}'.", level="INFO")
            log_message("These files will be checked against the destination for duplicates:", level="INFO")
            for f in latest_files_on_removable_media:
                log_message(f"- {f}", level="INFO")

            # This function now handles the duplicate check and conditional folder creation/copying
            check_and_copy_files(latest_files_on_removable_media, DESTINATION_BASE_DIR, most_recent_media_name)

        else:
            log_message(f"No .mp4 or .mov files found in '{full_source_path}'.", level="INFO")
            send_kodi_notification("Video Transfer", f"No videos found on '{most_recent_media_name}'.", image_type="info")
    else:
        log_message(f"No removable media detected in '{SOURCE_MEDIA_DIR}'.", level="WARNING")
        send_kodi_notification("Video Transfer", "No removable media found in /media. Nothing to transfer.", image_type="info")
