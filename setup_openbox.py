import subprocess
import logging
import os
from pathlib import Path
from datetime import datetime

TIME_STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_name = f'setup_openbox_{TIME_STAMP}'

# Set up logging
logging.basicConfig(filename=TIME_STAMP, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='w')

def run_command(command):
    """Runs a command, logs output, and handles errors."""
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        logging.info(f"Command: {' '.join(command)}\nOutput: {result.stdout}")

        if result.returncode != 0:
            logging.error(f"Error: {result.stderr}")

    except subprocess.CalledProcessError as e:
        logging.exception(f"Command execution failed: {e}")
        raise  # Re-raise to stop the script execution

# Get the username and home directory
user = os.getenv("USER")
home_dir = Path(os.getenv("HOME"))

# Update and install packages
run_command(["sudo", "apt", "update", "-y"])
run_command(["sudo", "apt", "upgrade", "-y"])
run_command(["sudo", "apt", "install", "-y", "openbox", "obconf", "lxterminal", "thunar", "obmenu"])

# Download and install Chrome Remote Desktop
run_command(["wget", "-qO", "-", "https://dl.google.com/linux/linux_signing_key.pub"])
run_command(["sudo", "apt-key", "add", "-"])
run_command(["sudo", "sh", "-c", 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome-remote-desktop/deb/ stable main" >> /etc/apt/sources.list.d/chrome-remote-desktop.list'])
run_command(["sudo", "apt", "update", "-y"])
run_command(["sudo", "apt", "install", "-y", "chrome-remote-desktop"])

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