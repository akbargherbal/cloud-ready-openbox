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
    print(f'Running: {" ".join(command)}')
    logging.info(f'Running: {" ".join(command)}')
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        if log_output:
            logging.info(f"Output: {result.stdout}")
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}\nError output: {e.stderr}")
        print(f"Command failed: {e}\nError output: {e.stderr}")
        return False

def install_packages(packages):
    """Installs a list of packages."""
    for package in packages:
        print(f"Installing {package}...")
        if not run_command(["sudo", "apt", "install", "-y", package]):
            logging.error(f"Failed to install {package}. Exiting script.")
            exit(1)
        print(f"{package} installed successfully.")

def setup_chrome_remote_desktop():
    """Sets up Chrome Remote Desktop."""
    print("Setting up Chrome Remote Desktop...")
    logging.info("Setting up Chrome Remote Desktop")

    # Add Chrome Remote Desktop repository and key
    if not run_command(["curl", "https://dl.google.com/linux/linux_signing_key.pub", 
                        "|", "sudo", "gpg", "--dearmor", "-o", "/etc/apt/trusted.gpg.d/chrome-remote-desktop.gpg"]):
        logging.error("Failed to download or add Google signing key. Exiting script.")
        print("Failed to download or add Google signing key. Exiting script.")
        exit(1)
    
    if not run_command(["sudo", "tee", "/etc/apt/sources.list.d/chrome-remote-desktop.list"], input="deb [arch=amd64] https://dl.google.com/linux/chrome-remote-desktop/deb stable main\n"):
        logging.error("Failed to add Chrome Remote Desktop repository. Exiting script.")
        print("Failed to add Chrome Remote Desktop repository. Exiting script.")
        exit(1)
    
    # Update package indexes and install Chrome Remote Desktop
    if not run_command(["sudo", "apt-get", "update"]) or \
       not run_command(["sudo", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "--assume-yes", "chrome-remote-desktop"]):
        logging.error("Failed to update package indexes or install Chrome Remote Desktop. Exiting script.")
        print("Failed to update package indexes or install Chrome Remote Desktop. Exiting script.")
        exit(1)
    print("Chrome Remote Desktop setup complete.")

def configure_openbox(user, home_dir):
    """Configures Openbox for the given user."""
    print("Configuring Openbox...")
    openbox_config_dir = home_dir / ".config" / "openbox"
    openbox_config_dir.mkdir(parents=True, exist_ok=True)
    run_command(["cp", "/etc/xdg/openbox/rc.xml", str(openbox_config_dir / "rc.xml")])
    run_command(["cp", "/etc/xdg/openbox/menu.xml", str(openbox_config_dir / "menu.xml")])

    session_file = home_dir / ".chrome-remote-desktop-session"
    with session_file.open("w") as f:
        f.write("exec openbox-session\n")
    
    run_command(["chmod", "+x", str(session_file)])
    print("Openbox configuration complete.")

def enable_crd_service(user):
    """Enables and starts the Chrome Remote Desktop service for the user."""
    print("Enabling and starting Chrome Remote Desktop service...")
    if not run_command(["sudo", "systemctl", "enable", f"chrome-remote-desktop@{user}"]) or \
       not run_command(["sudo", "systemctl", "start", f"chrome-remote-desktop@{user}"]):
        logging.error("Failed to enable or start Chrome Remote Desktop service. Exiting script.")
        print("Failed to enable or start Chrome Remote Desktop service. Exiting script.")
        exit(1)
    print("Chrome Remote Desktop service enabled and started.")

def main():
    print("Starting Openbox and Chrome Remote Desktop setup...")
    logging.info("Starting Openbox and Chrome Remote Desktop setup")

    user_info = pwd.getpwuid(os.getuid())
    user = user_info.pw_name
    home_dir = Path(user_info.pw_dir)

    logging.info(f"Setting up for user: {user}, home directory: {home_dir}")
    print(f"Setting up for user: {user}, home directory: {home_dir}")

    if not run_command(["sudo", "apt", "update"]) or \
       not run_command(["sudo", "apt", "upgrade", "-y"]):
        logging.error("Failed to update and upgrade packages. Exiting script.")
        print("Failed to update and upgrade packages. Exiting script.")
        exit(1)
    print("System packages updated and upgraded.")

    install_packages(["openbox", "obconf", "lxterminal", "thunar"])
    if run_command(["apt", "search", "obmenu"]):
        run_command(["sudo", "apt", "install", "-y", "obmenu"])

    setup_chrome_remote_desktop()

    # Create or ensure the 'chrome-remote-desktop' group exists
    run_command(["sudo", "groupadd", "-f", "chrome-remote-desktop"])
    if not run_command(["sudo", "usermod", "-a", "-G", "chrome-remote-desktop", user]):
        logging.error(f"Failed to add {user} to chrome-remote-desktop group. Exiting script.")
        print(f"Failed to add {user} to chrome-remote-desktop group. Exiting script.")
        exit(1)
    print(f"User {user} added to chrome-remote-desktop group.")

    configure_openbox(user, home_dir)
    enable_crd_service(user)

    logging.info("Openbox and Chrome Remote Desktop setup complete!")
    print("Openbox and Chrome Remote Desktop setup complete!")

if __name__ == "__main__":
    main()
