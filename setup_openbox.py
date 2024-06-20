import subprocess
import logging
import os
from pathlib import Path
from datetime import datetime

TIME_STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_name = f'setup_openbox_{TIME_STAMP}.log'

# Set up logging
logging.basicConfig(filename=log_file_name, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')

def run_command(command):
    """Runs a command, logs output, and handles errors."""
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        logging.info(f"Command: {' '.join(command)}\nOutput: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return None

# Get the username and home directory
user = os.getenv("USER")
home_dir = Path(os.getenv("HOME"))

if not user or not home_dir:
    logging.error("USER or HOME environment variables are not set. Exiting script.")
    print("USER or HOME environment variables are not set. Exiting script.")
    exit(1)

# Update package indexes and upgrade packages
if not run_command(["sudo", "apt", "update", "-y"]):
    logging.error("Failed to update package indexes. Exiting script.")
    exit(1)

if not run_command(["sudo", "apt", "upgrade", "-y"]):
    logging.error("Failed to upgrade packages. Exiting script.")
    exit(1)

# Install necessary packages for Openbox and menu generation
packages = ["openbox", "obconf", "thunar", "menu", "rofi", "tint2"]
for package in packages:
    if not run_command(["sudo", "apt", "install", "-y", package]):
        logging.error(f"Failed to install {package}. Exiting script.")
        print(f"Failed to install {package}. Exiting script.")
        exit(1)

logging.info("All packages installed successfully.")
print("All packages installed successfully.")

# Install Chrome Remote Desktop
if not run_command(["curl", "-sSL", "https://dl.google.com/linux/linux_signing_key.pub", "-o", "/tmp/linux_signing_key.pub"]):
    logging.error("Failed to download Chrome Remote Desktop signing key.")
    exit(1)

if not run_command(["sudo", "gpg", "--dearmor", "-o", "/etc/apt/trusted.gpg.d/chrome-remote-desktop.gpg", "/tmp/linux_signing_key.pub"]):
    logging.error("Failed to add Chrome Remote Desktop signing key.")
    exit(1)

if not run_command(["sudo", "sh", "-c", 'echo "deb [arch=amd64] https://dl.google.com/linux/chrome-remote-desktop/deb stable main" > /etc/apt/sources.list.d/chrome-remote-desktop.list']):
    logging.error("Failed to add Chrome Remote Desktop repository.")
    exit(1)

if not run_command(["sudo", "apt-get", "update"]):
    logging.error("Failed to update package indexes after adding Chrome Remote Desktop repository.")
    exit(1)

if not run_command(["sudo", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "--assume-yes", "chrome-remote-desktop"]):
    logging.error("Failed to install Chrome Remote Desktop.")
    exit(1)

# Configure Chrome Remote Desktop
if not run_command(["sudo", "groupadd", "chrome-remote-desktop"]):
    logging.info("Group 'chrome-remote-desktop' already exists or failed to create. Continuing...")
    print("Group 'chrome-remote-desktop' already exists or failed to create. Continuing...")

if not run_command(["sudo", "usermod", "-a", "-G", "chrome-remote-desktop", user]):
    logging.error(f"Failed to add user '{user}' to 'chrome-remote-desktop' group.")
    exit(1)

print(f"User '{user}' added to group 'chrome-remote-desktop' successfully.")
logging.info(f"User '{user}' added to group 'chrome-remote-desktop' successfully.")

# Prepare Openbox configuration
openbox_config_dir = home_dir / ".config" / "openbox"
openbox_config_dir.mkdir(parents=True, exist_ok=True)

if not run_command(["cp", "/etc/xdg/openbox/rc.xml", str(openbox_config_dir / "rc.xml")]):
    logging.error("Failed to copy Openbox configuration file.")
    exit(1)

print("Openbox configuration prepared successfully.")
logging.info("Openbox configuration prepared successfully.")

# Generate the menu using menu package and copy to Openbox config directory
if not run_command(["sudo", "update-menus"]):
    logging.error("Failed to generate menu. Exiting script.")
    print("Failed to generate menu. Exiting script.")
    exit(1)

if not run_command(["cp", "/etc/xdg/openbox/menu.xml", str(openbox_config_dir / "menu.xml")]):
    logging.error("Failed to copy menu to Openbox config directory.")
    exit(1)

print("Menu generated and copied to Openbox config directory successfully.")
logging.info("Menu generated and copied to Openbox config directory successfully.")

# Write Chrome Remote Desktop session file
session_file = home_dir / ".chrome-remote-desktop-session"
with session_file.open("w") as f:
    f.write("exec openbox-session\n")

# Set permissions on the session file
if not run_command(["chmod", "+x", str(session_file)]):
    logging.error("Failed to set permissions on Chrome Remote Desktop session file.")
    exit(1)

# Enable and start Chrome Remote Desktop service
if not run_command(["sudo", "systemctl", "enable", f"chrome-remote-desktop@{user}"]):
    logging.error("Failed to enable Chrome Remote Desktop service.")
    exit(1)

if not run_command(["sudo", "systemctl", "start", f"chrome-remote-desktop@{user}"]):
    logging.error("Failed to start Chrome Remote Desktop service.")
    exit(1)

print("Openbox and Chrome Remote Desktop setup complete!")
logging.info("Openbox and Chrome Remote Desktop setup complete!")
