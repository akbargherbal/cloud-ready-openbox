import subprocess
import logging
import os
from pathlib import Path
import sys
from datetime import datetime
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Set up Openbox and Chrome Remote Desktop")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
parser.add_argument("-l", "--log-file", default=None, help="Specify a custom log file path")
args = parser.parse_args()

# Set up logging
TIME_STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
if args.log_file:
    log_file_name = args.log_file
else:
    log_file_name = os.path.join(Path.home(), f'setup_openbox_{TIME_STAMP}.log')

log_level = logging.DEBUG if args.verbose else logging.INFO
logging.basicConfig(filename=log_file_name, level=log_level,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')

# Rest of your script...

def run_command(command, capture_output=False):
    """Runs a command, logs output, and handles errors."""
    try:
        logging.info(f"Running command: {' '.join(command)}")
        if capture_output:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True, capture_output=True)
            logging.debug(f"Output: {result.stdout}")
            logging.debug(f"Error output: {result.stderr}")
            return result.stdout, result.stderr
        else:
            subprocess.run(command, check=True)
            return True  # Success
    except subprocess.CalledProcessError as e:
        logging.error(f"Command execution failed: {e}")
        return False  # Failure

def install_packages(packages):
    """Install a list of packages using the system package manager."""
    for package in packages:
        logging.info(f"Installing {package}...")
        if not run_command(["sudo", "apt", "install", "-y", package]):
            logging.error(f"Failed to install {package}. Continuing installation...")
            return False
    return True

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

    # Install packages as a dependency group
    print("Installing Openbox and related packages...")
    packages = ["openbox", "obconf", "lxterminal", "thunar", "obm-menumaker"]
    if not install_packages(packages):
        logging.error("Failed to install Openbox and related packages.")
        sys.exit(1)

    # Download and install Chrome Remote Desktop
    print("Downloading and installing Chrome Remote Desktop...")
    if not run_command(["wget", "-qO", "-", "https://dl.google.com/linux/linux_signing_key.pub"], capture_output=True):
        logging.error("Failed to download Chrome Remote Desktop signing key. Continuing installation...")
        sys.exit(1)

    key_output, _ = run_command(["sudo", "apt-key", "add", "-"], capture_output=True, input=key_output.encode())
    if not key_output:
        logging.error("Failed to add Chrome Remote Desktop signing key. Continuing installation...")
        sys.exit(1)

    if not run_command(["sudo", "sh", "-c", 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome-remote-desktop/deb/ stable main" >> /etc/apt/sources.list.d/chrome-remote-desktop.list']):
        logging.error("Failed to add Chrome Remote Desktop repository. Continuing installation...")
        sys.exit(1)

    if not run_command(["sudo", "apt", "update", "-y"]):
        logging.error("Failed to update package indexes after adding Chrome Remote Desktop repository. Continuing installation...")
        sys.exit(1)

    if not install_packages(["chrome-remote-desktop"]):
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
    run_command(["obm-menumaker", "-o", str(openbox_config_dir / "menu.xml")])

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