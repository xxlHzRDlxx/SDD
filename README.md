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
- [Update Main Menu](#update-main-menu)
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

1. **Create the scripts directory:**
   Open an SSH session to your OSMC Vero V and create the dedicated scripts directory:

   ```bash
   mkdir -p ~/scripts/
