import os
import platform
import subprocess
import sys
import requests
import logging
from requests.auth import HTTPBasicAuth

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'setup.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def setup_task_scheduler(projects_dir):
    try:
        subprocess.run(f'setx GITHUB_AUTOSAVE_PROJECTS_DIR "{projects_dir}"', shell=True, check=True)
        subprocess.run(f'setx GITHUB_AUTOSAVE_CONFIG_FILE "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "autosave_config.txt")}"', shell=True, check=True)

        task_name = "Github Autosave"
        script_path = os.path.abspath("main.py")
        python_path = sys.executable

        # Create a task to run the autosave script every hour
        command = f"{python_path} {script_path}"
        subprocess.run(f'schtasks /create /tn "{task_name}" /tr "{command}" /sc hourly', shell=True, check=True)
        logging.info(f"Task created: {task_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set up task scheduler: {e}")
        sys.exit(1)

def run_autosave_script():
    try:
        script_path = os.path.abspath("main.py")
        python_path = sys.executable
        subprocess.run(f"{python_path} {script_path} --bypass-check", shell=True, check=True)
        logging.info("Autosave script executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to run autosave script: {e}")
        sys.exit(1)

def main():
    # Gather OS information
    os_name = platform.system()
    logging.info(f"OS: {os_name}")

    # Ensure git is installed and push.autoSetupRemote is set to true
    git_version = subprocess.run("git --version", shell=True)
    if git_version.returncode != 0:
        logging.error("Git is not installed. Please install git and try again.")
        sys.exit(1)

    try:
        subprocess.run("git config --global push.autoSetupRemote true", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to set git config: {e}")
        sys.exit(1)

    # Gather Projects information
    projects_dir = input("Enter the absolute path to the projects directory: ")
    projects_dir = os.path.abspath(projects_dir)
    if not os.path.exists(projects_dir):
        logging.error(f"Projects directory {projects_dir} does not exist. Please create it and try again.")
        sys.exit(1)
    logging.info(f"Projects directory: {projects_dir}")

    # Gather Github authentication information
    github_username = input("Enter your Github username (ex: johndoe): ")
    github_token = input("Enter your Github token: ")

    # Ensure github_token is valid
    auth_url = "https://api.github.com/user"
    response = requests.get(auth_url, auth=HTTPBasicAuth(github_username, github_token))

    if response.status_code != 200:
        logging.error("Invalid Github credentials. Please check your username and token and try again.")
        sys.exit(1)
    logging.info("Github credentials verified successfully.")

    # Gather OpenAI authentication information
    openai_key = input("Enter your OpenAI key: ")
    if openai_key:
        # Ensure openai_key is valid
        openai_auth_url = "https://api.openai.com/v1/engines"
        headers = {"Authorization": f"Bearer {openai_key}"}
        response = requests.get(openai_auth_url, headers=headers)

        if response.status_code != 200:
            logging.error("Invalid OpenAI key. Please check your key and try again.")
            sys.exit(1)
        logging.info("OpenAI key verified successfully.")
    else:
        logging.info("No OpenAI key provided. Skipping OpenAI authentication.")

    # Set up environment variables and config files
    logging.info("Setting up autosave!")
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autosave_config.txt")
    try:
        with open(config_file, "w") as f:
            f.write("[DEFAULT]\n")
            f.write(f"projects_dir={projects_dir}\n")
            f.write(f"github_username={github_username}\n")
            f.write(f"github_token={github_token}\n")
            f.write(f"openai_key={openai_key}\n")
            logging.info(f"Config file created at {config_file}")
    except IOError as e:
        logging.error(f"Failed to create config file: {e}")
        sys.exit(1)

    if os_name == "Windows":
        setup_task_scheduler(projects_dir)
    # elif os_name == "Linux":
    #     setup_systemd_service(projects_dir)
    # elif os_name == "Darwin":
    #     setup_launchd_service(projects_dir)
    else:
        logging.error("Unsupported OS")
        sys.exit(1)

    # Run the autosave script for the first time
    run_autosave_script()

    logging.info("Setup complete!")

if __name__ == "__main__":
    main()