This script, written in Python 3, automates the process of copying the latest video files from recently connected removable media (like USB drives) to a designated "Unsorted Videos" directory. It also provides real-time notifications on a Kodi media center about the transfer process.

Features
Automatic Media Detection: Identifies the most recently mounted removable media in the /media/ directory.
Latest Video Discovery: Scans the detected removable media for the 3 most recently modified .mp4 or .mov video files.
Duplicate Prevention: Before copying, it checks if the video files already exist in the destination directory or its subfolders to avoid duplicates.
Organized Archiving: Creates a new, timestamped subfolder within the destination directory for each transfer, named after the removable media (e.g., [USB_DRIVE_NAME] - YYYY-MM-DD HH-MM-SS).
Kodi Notifications: Sends on-screen notifications to Kodi, informing the user about:
Script execution.
Progress of video transfers (e.g., "1 of 3 new videos downloaded").
Completion of transfers.
Skipped files due to existing duplicates.
Errors during the process (e.g., no media found, Kodi connection issues, file copy failures).
Robust Error Handling: Includes comprehensive error handling for file operations, network requests to Kodi, and JSON parsing.
Logging: Records script execution timestamps to a download log file.
Prerequisites
Python 3: The script is written in Python 3.
requests library: Install using pip3 install requests.
Kodi: Must be running on localhost (the same machine where the script is executed).
Kodi JSON-RPC API Enabled: In Kodi settings, ensure "Allow remote control via HTTP" is enabled (Settings -> Services -> Control).
sudo privileges: The script uses sudo cp for copying files, which may require password elevation. Ensure the user running the script has appropriate sudo permissions without a password prompt for cp if running automatically.
Mount Point: Removable media are expected to be mounted under /media/.
Destination Directory: The script targets /mnt/unifi/Unsorted_Videos/ as the base destination for copied videos. Ensure this directory exists and the script has write permissions.
How it Works
Initialization:

Logs the current time to /home/osmc/scripts/download.log.
Defines the source_dir as /media/.
Sets allowed video extensions (.mp4, .mov).
Kodi Notification Function (send_kodi_notification):

Connects to Kodi's JSON-RPC API (default http://localhost:80/jsonrpc).
Sends GUI.ShowNotification requests with a specified title, message, display time, and image type.
Handles various network and JSON-related errors when communicating with Kodi.
Find Latest Videos (get_latest_mp4_files):

Recursively searches the given root_dir for .mp4 and .mov files.
Sorts the found files by their modification time to identify the latest ones.
Returns a specified count (defaulting to 3) of the most recent video file paths.
Identify Recent Removable Media (get_most_recent_removable_media):

Lists subdirectories within /media/.
Assumes the most recently modified subdirectory is the newly mounted removable media.
Returns the basename (folder name) of this media.
Check for Duplicates (find_file_in_unsorted_videos):

Performs a recursive search within the base_destination_path to see if a file with the given file_name already exists.
Copy Files (check_and_copy_files):

Iterates through the source_files (latest videos from removable media).
For each file, it calls find_file_in_unsorted_videos to check for duplicates in the destination.
If a file is new, it's added to a files_to_copy list. Kodi is notified if no new videos are found.
If there are files to copy, it creates a new subdirectory in /mnt/unifi/Unsorted_Videos/ named after the removable media and the current timestamp.
Uses subprocess.run(['sudo', 'cp', ...]) to copy each new file to the created destination folder.
Sends Kodi notifications for each successful copy and for overall progress.
Handles errors during the copying process.
Main Execution (if __name__ == "__main__":):

Calls get_most_recent_removable_media to find the source.
Calls get_latest_mp4_files on the detected media to get the videos to potentially copy.
Calls check_and_copy_files to perform the actual copying and duplicate checking logic.
Sends Kodi notifications based on whether media was found and if any video files were processed.
Usage
Save the script: Save the provided code as a Python file, e.g., video_transfer.py.

Make it executable: chmod +x video_transfer.py

Run the script: python3 video_transfer.py or ./video_transfer.py

It's recommended to set this script up as a cron job or a systemd service to run automatically when removable media is inserted or on a schedule.
Configuration
source_dir: Currently set to /media/. If your removable media mounts to a different base directory, update this variable.
VALID_EXTS: Defines the video file extensions to look for (.mp4, .mov). Add or remove extensions as needed.
base_destination_path: Set to /mnt/unifi/Unsorted_Videos/. Modify this to your desired video archive location.
get_latest_mp4_files(root_dir, count=3): The count parameter in this function determines how many of the latest video files are considered from the removable media. Adjust this number if you want to copy more or fewer recent files.
Kodi JSON-RPC URL: The kodi_rpc_url is http://localhost:80/jsonrpc. If your Kodi instance is on a different IP or port, update this URL.
Troubleshooting
"Error: Could not connect to Kodi...":
Ensure Kodi is running.
Verify "Allow remote control via HTTP" is enabled in Kodi's settings (Settings -> Services -> Control).
Check if Kodi's web server port (default 80) is not blocked by a firewall.
"Error copying... Permission denied":
The script uses sudo cp. Ensure the user running the script has the necessary sudo permissions to write to the base_destination_path. You might need to configure sudoers to allow passwordless execution of cp for this script's user if you intend to automate it.
Verify the base_destination_path (/mnt/unifi/Unsorted_Videos/) exists and has correct permissions.
"No removable media found in /media/":
Ensure your removable media is properly mounted and accessible under the /media/ directory.
Check if the media is formatted correctly and recognized by the OS.
"No .mp4 or .mov files found...":
Confirm that the video files on your removable media have the specified extensions and are not hidden.
Check if the files are indeed recent enough to be picked up by the get_latest_mp4_files function (which defaults to the 3 latest).
