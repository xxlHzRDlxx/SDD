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

# Get the current local date and time, including seconds
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open("/home/osmc/scripts/download.log", "a") as log:
    log.write(f"this script successfully ran {current_time}\n") # Added newline                                                                                                                                    for better logging

source_dir = "/media/"

def send_kodi_notification(title: str, message: str, displaytime_ms: int = 5000,                                                                                                                                    image_type: str = "info") -> bool:
    """
    Sends an on-screen notification to Kodi via its JSON-RPC API.

    Args:
        title (str): The title of the notification.
        message (str): The main message content of the notification.
        displaytime_ms (int): How long the notification should be displayed in m                                                                                                                                   illiseconds.
                              Default is 5000ms (5 seconds).
        image_type (str): The type of image/icon to display with the notificatio                                                                                                                                   n.
                          Common built-in Kodi icons include "info", "warning",                                                                                                                                    "error".
                          You can also specify a path to a custom image file if                                                                                                                                    accessible by Kodi.

    Returns:
        bool: True if the notification was sent successfully, False otherwise.
    """
    # The default JSON-RPC endpoint for Kodi running on the same machine.
    # Ensure Kodi's "Allow remote control via HTTP" is enabled in Settings -> Se                                                                                                                                   rvices -> Control.
    kodi_rpc_url = "http://localhost:80/jsonrpc"
    headers = {'Content-Type': 'application/json'}

    # Construct the JSON-RPC payload for the GUI.ShowNotification method.
    payload = {
        "jsonrpc": "2.0",
        "method": "GUI.ShowNotification",
        "params": {
            "title": title,
            "message": message,
            "displaytime": displaytime_ms,
            "image": image_type
        },
        "id": 1  # A unique ID for the request, can be any number.
    }

    try:
        # Send the POST request to the Kodi JSON-RPC API.
        response = requests.post(kodi_rpc_url, headers=headers, data=json.dumps(                                                                                                                                   payload), timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx o                                                                                                                                   r 5xx).

        # Parse the JSON response from Kodi.
        result = response.json()

        # Check if Kodi returned an error in its response.
        if 'error' in result:
            print(f"Error from Kodi API: {result['error']['message']}", file=sys                                                                                                                                   .stderr)
            return False
        else:
            print("Notification sent successfully.")
            return True

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Kodi. Please ensure Kodi is running a                                                                                                                                   nd its web server/JSON-RPC is enabled (Settings -> Services -> Control).", file=                                                                                                                                   sys.stderr)
        return False
    except requests.exceptions.Timeout:
        print("Error: Request to Kodi timed out. Kodi might be busy or unreachab                                                                                                                                   le.", file=sys.stderr)
        return False
    except requests.exceptions.RequestException as e:
        # Catch any other requests-related errors.
        print(f"An unexpected error occurred while sending the request: {e}", fi                                                                                                                                   le=sys.stderr)
        return False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON response from Kodi. Response: {resp                                                                                                                                   onse.text}", file=sys.stderr)
        return False

VALID_EXTS = [".mp4", ".mov"] # Lowercase with `.`
def get_latest_mp4_files(root_dir, count=3):
    """Finds the 'count' latest .mp4 or .mov files in any subdirectory of root_d                                                                                                                                   ir."""
    file_list = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            fileExt = os.path.splitext(file)[1]
            if fileExt.lower() in VALID_EXTS:
                file_path = os.path.join(root, file)
                modified_time = os.path.getmtime(file_path)
                file_list.append((file_path, modified_time))

    # Sort by modification time (newest first)
    file_list.sort(key=lambda item: item[1], reverse=True)
    return [item[0] for item in file_list[:count]]

def get_most_recent_removable_media(media_root_dir):
    """
    Identifies the most recently added removable storage in the specified media                                                                                                                                    root directory.
    Assumes removable media are subdirectories within media_root_dir.
    """
    try:
        subdirectories = [os.path.join(media_root_dir, d) for d in os.listdir(me                                                                                                                                   dia_root_dir) if os.path.isdir(os.path.join(media_root_dir, d))]
        if not subdirectories:
            return None

        # Sort subdirectories by their modification time (most recent first)
        subdirectories.sort(key=os.path.getmtime, reverse=True)

        # The most recently modified subdirectory is likely the most recently ad                                                                                                                                   ded media
        most_recent_media_path = subdirectories[0]
        return os.path.basename(most_recent_media_path)
    except FileNotFoundError:
        print(f"Error: Source directory '{media_root_dir}' not found.", file=sys                                                                                                                                   .stderr)
        return None
    except Exception as e:
        print(f"An error occurred while finding removable media: {e}", file=sys.                                                                                                                                   stderr)
        return None

def find_file_in_unsorted_videos(file_name, unsorted_videos_base_dir):
    """
    Checks if a file with file_name exists anywhere within the unsorted_videos_b                                                                                                                                   ase_dir
    or its subdirectories.
    """
    for root, _, files in os.walk(unsorted_videos_base_dir):
        if file_name in files:
            return True
    return False

def check_and_copy_files(source_files, base_destination_path):
    """
    Checks if source files exist anywhere within the base_destination_path (incl                                                                                                                                   uding subdirectories).
    If a file does not exist, it's added to a list for copying.
    If there are files to copy, a new folder is created in base_destination_path                                                                                                                                   , and files are copied there.
    """
    files_to_copy = []

    for source_file in source_files:
        file_name = os.path.basename(source_file)
        if not find_file_in_unsorted_videos(file_name, base_destination_path):
            files_to_copy.append(source_file)
        else:
            print(f"Skipped: '{file_name}' already exists in '{base_destination_                                                                                                                                   path}' or its subdirectories.")

    if not files_to_copy:
        send_kodi_notification("Video Transfer", "No new videos to download. All                                                                                                                                    checked videos already exist.", image_type="info")
        return

    # If there are files to copy, create a new folder with a timestamp
    current_datetime_str = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    most_recent_media_name = get_most_recent_removable_media(source_dir) # Re-ge                                                                                                                                   t this for the folder name
    destination_folder_name = f"{most_recent_media_name} - {current_datetime_str                                                                                                                                   }" if most_recent_media_name else f"Unsorted - {current_datetime_str}"
    destination_dir = os.path.join(base_destination_path, destination_folder_nam                                                                                                                                   e)

    os.makedirs(destination_dir, exist_ok=True) # Ensure new destination directo                                                                                                                                   ry exists

    copied_count = 0
    total_files_to_copy = len(files_to_copy)

    for source_file in files_to_copy:
        file_name = os.path.basename(source_file)
        destination_file_path = os.path.join(destination_dir, file_name)
        try:
            subprocess.run(['sudo', 'cp', source_file, destination_file_path], c                                                                                                                                   heck=True)
            copied_count += 1
            print(f"Copied: {source_file} to {destination_dir}")
            send_kodi_notification("Video Transfer", f"{copied_count} of {total_                                                                                                                                   files_to_copy} new videos downloaded.")
        except subprocess.CalledProcessError as e:
            print(f"Error copying {source_file}: {e}", file=sys.stderr)
            send_kodi_notification("File Transfer Failed", f"Failed to copy: {fi                                                                                                                                   le_name}", image_type="error")
        except Exception as e:
            print(f"An unexpected error occurred while copying {source_file}: {e                                                                                                                                   }", file=sys.stderr)
            send_kodi_notification("File Transfer Failed", f"Unexpected error co                                                                                                                                   pying: {file_name}", image_type="error")

    if copied_count > 0:
        send_kodi_notification("Video Transfer", f"Successfully copied {copied_c                                                                                                                                   ount} new videos to '{destination_folder_name}'.", image_type="info")
    else:
        send_kodi_notification("Video Transfer", "No new videos were copied.", i                                                                                                                                   mage_type="info")


if __name__ == "__main__":
    most_recent_media_name = get_most_recent_removable_media(source_dir)
    base_destination_path = "/mnt/unifi/Unsorted_Videos/"

    if most_recent_media_name:
        print(f"Most recently added removable media: {most_recent_media_name}")

        # Get the latest files from the removable media
        latest_files_on_removable_media = get_latest_mp4_files(os.path.join(sour                                                                                                                                   ce_dir, most_recent_media_name))

        if latest_files_on_removable_media:
            print(f"Checking these files from removable media against '{base_des                                                                                                                                   tination_path}':")
            for f in latest_files_on_removable_media:
                print(f"- {f}")

            # This function now handles the duplicate check and conditional fold                                                                                                                                   er creation/copying
            check_and_copy_files(latest_files_on_removable_media, base_destinati                                                                                                                                   on_path)

        else:
            print(f"No .mp4 or .mov files found in {os.path.join(source_dir, mos                                                                                                                                   t_recent_media_name)}.")
            send_kodi_notification("Video Transfer", f"No .mp4 or .mov files fou                                                                                                                                   nd on {most_recent_media_name} for transfer.", image_type="info")
    else:
        print(f"No removable media found in {source_dir}.")
        send_kodi_notification("Video Transfer", "No removable media found.", im                                                                                                                                   age_type="info")
