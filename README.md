# OSMC Video Transfer Script

This repository contains a Python script designed to automate the transfer of video files from a connected USB drive (or SD card) to a Network Attached Storage (NAS) accessible by your OSMC device. The script is specifically tailored for a Linux Vero V OSMC box and integrates with Kodi through keymapping for easy execution.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Script Placement](#script-placement)
  - [NAS Mounting (AutoFS)](#nas-mounting-autofs)
  - [Kodi Keymapping](#kodi-keymapping)
- [Usage](#usage)
- [Logging](#logging)
- [Configuration](#configuration)
- [Script Details](#script-details)
- [Troubleshooting](#troubleshooting)

## Overview

When a USB drive or SD card containing video files is inserted into your OSMC Vero V, this script, when triggered, will automatically identify the most recently connected media. It then scans for video files (currently `.mp4` and `.mov` are supported) and copies any new files to a designated folder on your NAS. Duplicate files are handled by appending a date and an incrementing counter to the filename to prevent overwrites. Kodi notifications provide real-time feedback on the transfer process.

## Features

- **Automated Media Detection:** Identifies the most recently mounted removable media.
- **Video File Filtering:** Specifically looks for `.mp4` and `.mov` video files.
- **Duplicate Prevention:** Renames files with a date and counter (e.g., `MyVideo - 2023-10-27 - 1.mp4`) to avoid overwriting existing files on the NAS.
- **Kodi Integration:** Provides on-screen notifications via Kodi's JSON-RPC API for transfer status.
- **Robust Logging:** Maintains a detailed log of all actions, including success, skips, and errors.
- **File Name Cleaning:** Automatically removes problematic `._` prefixes and single quotes from filenames, common with files copied from HFS+ formatted devices.
- **`sudo` Copying:** Uses `sudo cp` for file transfers to ensure proper permissions are handled when writing to the NAS.

## Prerequisites

Before setting up and using this script, ensure you have:

- An **OSMC Vero V** running the OSMC operating system.
- Basic familiarity with SSH and the Linux command line.
- A **NAS** accessible from your OSMC device.
- Kodi's web server and JSON-RPC API enabled (Settings -> Services -> Control).

## Installation

### Script Placement

1.  **Create the scripts directory:**
    Open an SSH session to your OSMC Vero V and create the dedicated scripts directory:

    ```bash
    mkdir -p ~/scripts/
    ```

2.  **Download the script and log file:**
    Place the `download.py` script (the Python code provided below) and an empty `download.log` file into this `~/scripts/` directory.

    For example, you can use `nano` to create the `download.py` file:

    ```bash
    nano ~/scripts/download.py
    ```

    Paste the Python script into the `nano` editor, then save and exit (Ctrl+X, Y, Enter).

    Create the empty log file:

    ```bash
    touch ~/scripts/download.log
    ```

3.  **Make the script executable:**

    ```bash
    chmod +x ~/scripts/download.py
    ```

### NAS Mounting (AutoFS)

The script assumes your NAS is mounted to `/mnt/unifi` using AutoFS. If you haven't set this up yet, please follow the official OSMC documentation for mounting network shares with AutoFS:

[OSMC Wiki: Mounting network shares with autofs (alternative to fstab)](https://osmc.tv/wiki/general/mounting-network-shares-with-autofs-alternative-to-fstab/)

Ensure your AutoFS configuration results in your NAS being mounted at `/mnt/unifi`. The `/etc/auto.smb.shares` file used for this setup is:

```/mnt/unifi/ -fstype=cifs,rw,credentials=/home/osmc/.smbcredentials,iocharset=utf8,uid=osmc,gid=osmc,vers=3.0 ://192.168.1.38/Fun_Jumpers/Video```

The credentials file (`/home/osmc/.smbcredentials`) should contain your NAS username and password in the format `username=osmc` and `password=YOUR_PASSWORD`. The password can be reset by an admin.

### Kodi Keymapping

The script is designed to be triggered by a long-press of the `[` (left bracket) key on your keyboard (or OSMC remote, if mapped). This is achieved through Kodi's keymapping feature.

1.  **Create the keymap directory (if it doesn't exist):**

    ```bash
    mkdir -p ~/.kodi/userdata/keymaps/osmc/
    ```

2.  **Create or edit the `gen.xml` file:**
    Use `nano` to create or edit the `gen.xml` file in the keymaps directory:

    ```bash
    nano ~/.kodi/userdata/keymaps/osmc/gen.xml
    ```

3.  **Add the keymap configuration:**
    Paste the following XML content into the `gen.xml` file. This configures a long-press of the left bracket key to run the `download.py` script.

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <keymap>
    <global>
    <keyboard>
    <leftbracket mod="longpress">RunScript(/home/osmc/scripts/download.py)</leftbracket>
    </keyboard>
    </global>
    <FullscreenVideo>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </FullscreenVideo>
    <FullscreenGame>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </FullscreenGame>
    <FullscreenInfo>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </FullscreenInfo>
    <Visualisation>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </Visualisation>
    <MusicOSD>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </MusicOSD>
    <VisualisationPresetList>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </VisualisationPresetList>
    <VideoOSD>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </VideoOSD>
    <VideoMenu>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </VideoMenu>
    <OSDVideoSettings>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </OSDVideoSettings>
    <OSDAudioSettings>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </OSDAudioSettings>
    <osdsubtitlesettings>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </osdsubtitlesettings>
    <MusicInformation>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </MusicInformation>
    <SongInformation>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </SongInformation>
    <MovieInformation>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </MovieInformation>
    <PictureInfo>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </PictureInfo>
    <FullscreenLiveTV>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </FullscreenLiveTV>
    <AddonInformation>
    <keyboard>
    <leftbracket mod="longpress"/>
    </keyboard>
    </AddonInformation>
    </keymap>
    ```
    Save and exit `nano`.

4.  **Reboot Kodi:** To apply the new keymap, you need to reboot Kodi. You can do this by rebooting the entire OSMC device:

    ```bash
    sudo reboot
    ```

    For detailed information on OSMC remote long-press keymap, refer to:
    [OSMC Wiki: OSMC Remote - Long-press keymap guide](https://osmc.tv/wiki/general/osmc-remote---long-press-keymap-guide/)

## Usage

1.  Insert your USB drive or SD card into your OSMC Vero V.
2.  From within Kodi, perform a **long-press** on the `[` (left bracket) key.
3.  The script will start running in the background. You will receive Kodi notifications about the progress of the video transfer.

## Logging

All script activities, including successful copies, skipped files, and errors, are logged to:
`~/scripts/download.log`

You can view this log file via SSH to monitor the script's operation:

```bash
cat ~/scripts/download.log
