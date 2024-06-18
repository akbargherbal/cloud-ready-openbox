# GCP Openbox Setup Script

This Python script automates the installation and configuration of Openbox window manager and Chrome Remote Desktop on a Google Cloud Platform (GCP) virtual machine (VM) instance.

## Prerequisites

* A GCP account and a running VM instance (Debian/Ubuntu based).
* SSH access to your VM instance.
* Python 3 installed on the VM instance.

## Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/akbargherbal/gcp-openbox-setup.git
   ```

2. **Navigate to the script directory:**
   ```bash
   cd gcp-openbox-setup
   ```


3. **Run the script:**
   ```bash
   python3 setup_openbox.py 
   ```

## What the Script Does

* Updates and upgrades system packages.
* Installs Openbox, a terminal emulator (lxterminal), and a file manager (Thunar).
* Downloads and installs Chrome Remote Desktop.
* Configures Chrome Remote Desktop to automatically start an Openbox session. 

## Notes

* This script assumes you're using the default user account or have `sudo` access.
* After running the script, you can connect to your VM using Chrome Remote Desktop ([https://remotedesktop.google.com/](https://remotedesktop.google.com/)).
* The script includes basic error handling and logging; check the `setup_openbox.log` file for details if something goes wrong.

## Customization

You can customize the Openbox configuration further by modifying the files in the `~/.config/openbox/` directory. 
