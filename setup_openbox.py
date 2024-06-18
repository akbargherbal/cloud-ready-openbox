import subprocess
import logging
import os
from pathlib import Path
import sys
from datetime import datetime

# Set up logging
TIME_STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_name = os.path.join(os.getenv("HOME"), f'setup_openbox_{TIME_STAMP}.log')

logging.basicConfig(filename=log_file_name, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')

def run_command(command):
    """Runs a command, logs output, and handles errors."""
    try:
        logging.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        logging.info(f"Output: {result.stdout}")
        return True  # Success
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False  # Failure

# Ensure script runs with appropriate permissions (e.g., sudo)
if os.geteuid() != 0:
    logging.error("Script must be run with sudo or as root.")
    sys.exit(1)

# Main installation steps
try:
    print("Starting Openbox and Chrome Remote Desktop setup...")

    # Update package indexes
    print("Updating package indexes...")
    if not run_command(["sudo", "apt", "update", "-y"]):
        logging.error("Failed to update package indexes. Continuing installation...")

    # Upgrade packages
    print("Upgrading packages...")
    if not run_command(["sudo", "apt", "upgrade", "-y"]):
        logging.error("Failed to upgrade packages. Continuing installation...")

    # Install packages individually
    print("Installing Openbox and related packages...")
    packages = ["openbox", "obconf", "lxterminal", "thunar", "menumaker"]
    for package in packages:
        if not run_command(["sudo", "apt", "install", "-y", package]):
            logging.error(f"Failed to install {package}. Continuing installation...")
            sys.exit(1)

    # Download and install Chrome Remote Desktop
    print("Downloading and installing Chrome Remote Desktop...")
    if not run_command(["wget", "-qO", "-", "https://dl.google.com/linux/linux_signing_key.pub"]):
        logging.error("Failed to download Chrome Remote Desktop signing key. Continuing installation...")
        sys.exit(1)

    if not run_command(["sudo", "apt-key", "add", "-"]):
        logging.error("Failed to add Chrome Remote Desktop signing key. Continuing installation...")
        sys.exit(1)

    if not run_command(["sudo", "sh", "-c", 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome-remote-desktop/deb/ stable main" >> /etc/apt/sources.list.d/chrome-remote-desktop.list']):
        logging.error("Failed to add Chrome Remote Desktop repository. Continuing installation...")
        sys.exit(1)

    if not run_command(["sudo", "apt", "update", "-y"]):
        logging.error("Failed to update package indexes after adding Chrome Remote Desktop repository. Continuing installation...")
        sys.exit(1)

    if not run_command(["sudo", "apt", "install", "-y", "chrome-remote-desktop"]):
        logging.error("Failed to install Chrome Remote Desktop. Continuing installation...")
        sys.exit(1)

    # Configure Chrome Remote Desktop
    print("Configuring Chrome Remote Desktop...")
    try:
        run_command(["sudo", "groupadd", "chrome-remote-desktop"])
    except subprocess.CalledProcessError:
        logging.info("Group 'chrome-remote-desktop' already exists. Continuing...")

    user = os.getenv("USER")
    run_command(["sudo", "usermod", "-a", "-G", "chrome-remote-desktop", user])

    # Prepare Openbox configuration
    print("Preparing Openbox configuration...")
    home_dir = Path(os.getenv("HOME"))
    openbox_config_dir = home_dir / ".config" / "openbox"
    openbox_config_dir.mkdir(parents=True, exist_ok=True)
    run_command(["cp", "/etc/xdg/openbox/rc.xml", str(openbox_config_dir / "rc.xml")])
    run_command(["menumaker", "-f", "-t", "openbox3", "-o", str(openbox_config_dir / "menu.xml")])

    # Write Chrome Remote Desktop session file
    print("Setting up Chrome Remote Desktop session...")
    session_file = home_dir / ".chrome-remote-desktop-session"
    with session_file.open("w") as f:
        f.write("exec openbox-session\n")

    # Set permissions on the session file
    run_command(["chmod", "+x", str(session_file)])

    # Enable and start Chrome Remote Desktop service
    print("Enabling and starting Chrome Remote Desktop service...")
    run_command(["sudo", "systemctl", "enable", f"chrome-remote-desktop@{user}"])
    run_command(["sudo", "systemctl", "start", f"chrome-remote-desktop@{user}"])

    print("Openbox and Chrome Remote Desktop setup complete!")
    logging.info("Openbox and Chrome Remote Desktop setup complete!")

except Exception as ex:
    logging.error(f"Unexpected error occurred: {ex}")
    sys.exit(1)
