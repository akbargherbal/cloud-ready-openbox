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
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False
    return True

# Get the username and home directory
user = os.getenv("USER")
home_dir = Path(os.getenv("HOME"))

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
        
# Install Chrome Remote Desktop
try:
    run_command(["curl", "https://dl.google.com/linux/linux_signing_key.pub", "|", "sudo", "gpg", "--dearmor", "-o", "/etc/apt/trusted.gpg.d/chrome-remote-desktop.gpg"])
    run_command(["echo", "\"deb [arch=amd64] https://dl.google.com/linux/chrome-remote-desktop/deb stable main\"", "|", "sudo", "tee", "/etc/apt/sources.list.d/chrome-remote-desktop.list"])
    run_command(["sudo", "apt-get", "update"])
    run_command(["sudo", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "--assume-yes", "chrome-remote-desktop"])
except subprocess.CalledProcessError as e:
    logging.error(f"Failed to install Chrome Remote Desktop: {e}")
    exit(1)

# Configure Chrome Remote Desktop
try:
    run_command(["sudo", "groupadd", "chrome-remote-desktop"])
except subprocess.CalledProcessError:
    logging.info("Group 'chrome-remote-desktop' already exists. Continuing...")

run_command(["sudo", "usermod", "-a", "-G", "chrome-remote-desktop", user])

# Prepare Openbox configuration
openbox_config_dir = home_dir / ".config" / "openbox"
openbox_config_dir.mkdir(parents=True, exist_ok=True)
run_command(["cp", "/etc/xdg/openbox/rc.xml", str(openbox_config_dir / "rc.xml")])

# Generate the menu using menu package and copy to Openbox config directory
if not run_command(["sudo", "update-menus"]):
    logging.error("Failed to generate menu. Exiting script.")
    exit(1)

run_command(["cp", "/etc/xdg/openbox/menu.xml", str(openbox_config_dir / "menu.xml")])

# Write Chrome Remote Desktop session file
session_file = home_dir / ".chrome-remote-desktop-session"
with session_file.open("w") as f:
    f.write("exec openbox-session\n")

# Set permissions on the session file
run_command(["chmod", "+x", str(session_file)])

# Enable and start Chrome Remote Desktop service
run_command(["sudo", "systemctl", "enable", f"chrome-remote-desktop@{user}"])
run_command(["sudo", "systemctl", "start", f"chrome-remote-desktop@{user}"])

print("Openbox and Chrome Remote Desktop setup complete!")
logging.info("Openbox and Chrome Remote Desktop setup complete!")
