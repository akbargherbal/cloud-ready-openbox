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
packages = ["openbox", "terminator" , "obconf", "thunar", "menu", "rofi",
            "tint2", "mousepad", "python3-pip", ]
for package in packages:
    if not run_command(["sudo", "apt", "install", "-y", package]):
        logging.error(f"Failed to install {package}. Exiting script.")
        print(f"Failed to install {package}. Exiting script.")
        exit(1)
    print(f"{package} installed successfully.")

logging.info("All packages installed successfully.")
print("All packages installed successfully.")


print(f'Downloading rofi themes')
try:
    run_command(["git", "clone", "https://github.com/lr-tech/rofi-themes-collection.git"])
    run_command(["mkdir", "-p", f"{home_dir}/.local/share/rofi/themes"])
    run_command(["cp", "-r", "themes/*", f"{home_dir}/.local/share/rofi/themes"])
    print(f'Rofi themes downloaded successfully.')
    logging.info(f'Rofi themes downloaded successfully.')
    print("Search for your desired theme, press enter to preview, then Alt+a to accept the new theme.")
    print('''
For terminator themes; check:
https://github.com/EliverLara/terminator-themes          
''')
except subprocess.CalledProcessError as e:
    logging.error(f"Failed to download rofi themes: {e}")
    print(f"Failed to download rofi themes: {e}")


chrom_installation = r'''
curl https://dl.google.com/linux/linux_signing_key.pub \
    | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/chrome-remote-desktop.gpg
echo "deb [arch=amd64] https://dl.google.com/linux/chrome-remote-desktop/deb stable main" \
    | sudo tee /etc/apt/sources.list.d/chrome-remote-desktop.list
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive \
    apt-get install --assume-yes chrome-remote-desktop
'''.strip()


print(f'''
To install Google Chrome Remote Desktop, run the following command:
========================================

{chrom_installation}

========================================
''')
