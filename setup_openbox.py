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

print("Updating package indexes...")
# Update package indexes
if not run_command(["sudo", "apt", "update", "-y"]):
    logging.error("Failed to update package indexes. Exiting script.")
    exit(1)

print("Upgrading packages...")
# Upgrade packages
if not run_command(["sudo", "apt", "upgrade", "-y"]):
    logging.error("Failed to upgrade packages. Exiting script.")
    exit(1)

print("Installing Openbox and related packages...")
# Install packages individually
packages = ["openbox", "obconf", "lxterminal", "thunar", "obmenu"]
for package in packages:
    if not run_command(["sudo", "apt", "install", "-y", package]):
        logging.error(f"Failed to install {package}. Exiting script.")
        exit(1)

print("Downloading and installing Chrome Remote Desktop...")
# Download and install Chrome Remote Desktop
if not run_command(["wget", "-qO", "-", "https://dl.google.com/linux/linux_signing_key.pub"]):
    logging.error("Failed to download Chrome Remote Desktop signing key. Exiting script.")
    exit(1)

if not run_command(["sudo", "apt-key", "add", "-"]):
    logging.error("Failed to add Chrome Remote Desktop signing key. Exiting script.")
    exit(1)

if not run_command(["sudo", "sh", "-c", 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome-remote-desktop/deb/ stable main" >> /etc/apt/sources.list.d/chrome-remote-desktop.list']):
    logging.error("Failed to add Chrome Remote Desktop repository. Exiting script.")
    exit(1)

if not run_command(["sudo", "apt", "update", "-y"]):
    logging.error("Failed to update package indexes after adding Chrome Remote Desktop repository. Exiting script.")
    exit(1)

if not run_command(["sudo", "apt", "install", "-y", "chrome-remote-desktop"]):
    logging.error("Failed to install Chrome Remote Desktop. Exiting script.")
    exit(1)

print("Configuring Chrome Remote Desktop...")
# Configure Chrome Remote Desktop
try:
    run_command(["sudo", "groupadd", "chrome-remote-desktop"])
except subprocess.CalledProcessError:
    logging.info("Group 'chrome-remote-desktop' already exists. Continuing...")

run_command(["sudo", "usermod", "-a", "-G", "chrome-remote-desktop", user])

print("Preparing Openbox configuration...")
# Prepare Openbox configuration
openbox_config_dir = home_dir / ".config" / "openbox"
openbox_config_dir.mkdir(parents=True, exist_ok=True)
run_command(["cp", "/etc/xdg/openbox/rc.xml", str(openbox_config_dir / "rc.xml")])
run_command(["cp", "/etc/xdg/openbox/menu.xml", str(openbox_config_dir / "menu.xml")])

print("Setting up Chrome Remote Desktop session...")
# Write Chrome Remote Desktop session file
session_file = home_dir / ".chrome-remote-desktop-session"
with session_file.open("w") as f:
    f.write("exec openbox-session\n")

# Set permissions on the session file
run_command(["chmod", "+x", str(session_file)])

print("Enabling and starting Chrome Remote Desktop service...")
# Enable and start Chrome Remote Desktop service
run_command(["sudo", "systemctl", "enable", f"chrome-remote-desktop@{user}"])
run_command(["sudo", "systemctl", "start", f"chrome-remote-desktop@{user}"])

print("Openbox and Chrome Remote Desktop setup complete!")
logging.info("Openbox and Chrome Remote Desktop setup complete!")