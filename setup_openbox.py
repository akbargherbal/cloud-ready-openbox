import subprocess
import logging
import os
from pathlib import Path
from datetime import datetime
import pwd

# Set up logging
TIME_STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_name = f'setup_openbox_{TIME_STAMP}.log'
logging.basicConfig(filename=log_file_name, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')

def run_command(command, log_output=True):
    """Runs a command, logs output, and handles errors."""
    print(f'Now Running: {" ".join(command)}')
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        if log_output:
            logging.info(f"Command: {' '.join(command)}\nOutput: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False
    return True

# Get current user info
user_info = pwd.getpwuid(os.getuid())
user = user_info.pw_name
home_dir = Path(user_info.pw_dir)

logging.info(f"Setting up for user: {user}, home directory: {home_dir}")

# Update package indexes
if not run_command(["sudo", "apt", "update"]):
    logging.error("Failed to update package indexes. Exiting script.")
    exit(1)

# Upgrade packages
if not run_command(["sudo", "apt", "upgrade", "-y"]):
    logging.error("Failed to upgrade packages. Exiting script.")
    exit(1)

# Install packages individually
packages = ["openbox", "obconf", "lxterminal", "thunar"]
for package in packages:
    if not run_command(["sudo", "apt", "install", "-y", package]):
        logging.error(f"Failed to install {package}. Exiting script.")
        exit(1)

# Check if obmenu is available before attempting to install
if run_command(["apt", "search", "obmenu"]):
    # Install obmenu if available
    if not run_command(["sudo", "apt", "install", "-y", "obmenu"]):
        logging.warning("obmenu found but installation failed.")

# Add the Chrome Remote Desktop repository
if not run_command(["sudo", "sh", "-c", 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome-remote-desktop/deb/ stable main" >> /etc/apt/sources.list.d/chrome-remote-desktop.list']):
    logging.error("Failed to add Chrome Remote Desktop repository. Exiting script.")
    exit(1)

# Import the Google Chrome Remote Desktop signing key
if not run_command(["wget", "-qO", "-", "https://dl.google.com/linux/linux_signing_key.pub", "|", "sudo", "apt-key", "add", "-"]):
    logging.error("Failed to import Google Chrome Remote Desktop signing key. Exiting script.")
    exit(1)

# Update package indexes after adding Chrome Remote Desktop repository
if not run_command(["sudo", "apt", "update"]):
    logging.error("Failed to update package indexes after adding Chrome Remote Desktop repository. Exiting script.")
    exit(1)

# Install Chrome Remote Desktop
if not run_command(["sudo", "apt", "install", "-y", "chrome-remote-desktop"]):
    logging.error("Failed to install Chrome Remote Desktop. Exiting script.")
    exit(1)

# Create or ensure the 'chrome-remote-desktop' group exists
run_command(["sudo", "groupadd", "-f", "chrome-remote-desktop"])

# Add the current user to the group
if not run_command(["sudo", "usermod", "-a", "-G", "chrome-remote-desktop", user]):
    logging.error(f"Failed to add {user} to chrome-remote-desktop group. Exiting script.")
    exit(1)

# Prepare Openbox configuration
openbox_config_dir = home_dir / ".config" / "openbox"
openbox_config_dir.mkdir(parents=True, exist_ok=True)
run_command(["cp", "/etc/xdg/openbox/rc.xml", str(openbox_config_dir / "rc.xml")])
run_command(["cp", "/etc/xdg/openbox/menu.xml", str(openbox_config_dir / "menu.xml")])

# Write Chrome Remote Desktop session file
session_file = home_dir / ".chrome-remote-desktop-session"
with session_file.open("w") as f:
    f.write("exec openbox-session\n")

# Set permissions on the session file
if not run_command(["chmod", "+x", str(session_file)]):
    logging.error(f"Failed to set execute permission on {session_file}. Exiting script.")
    exit(1)

# Enable and start Chrome Remote Desktop service
if not run_command(["sudo", "systemctl", "enable", f"chrome-remote-desktop@{user}"]):
    logging.error("Failed to enable Chrome Remote Desktop service. Exiting script.")
    exit(1)

if not run_command(["sudo", "systemctl", "start", f"chrome-remote-desktop@{user}"]):
    logging.error("Failed to start Chrome Remote Desktop service. Exiting script.")
    exit(1)

print("Openbox and Chrome Remote Desktop setup complete!")
logging.info("Openbox and Chrome Remote Desktop setup complete!")
