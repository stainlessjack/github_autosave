import os
import sys
import datetime
import logging
from autosave import autosave

from utils import load_config
import git_operations

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'autosave_{datetime.datetime.now().strftime("%Y%m%d")}.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Ensure the GITHUB_AUTOSAVE_CONFIG_FILE environment variable is set
if 'GITHUB_AUTOSAVE_CONFIG_FILE' not in os.environ:
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autosave_config.txt")
    os.environ['GITHUB_AUTOSAVE_CONFIG_FILE'] = config_file
else:
    config_file = os.environ['GITHUB_AUTOSAVE_CONFIG_FILE']

# Verify that the config file exists
if not os.path.exists(config_file):
    logging.error(f"Config file not found: {config_file}")
    raise FileNotFoundError(f"Config file not found: {config_file}")

def process_project(project_path, github_username, github_token, openai_key, bypass_check=False):
    """Process a single project directory, autosaving where necessary"""
    
    # Check if the project is a git repository
    if git_operations.is_git_repo(project_path):
        # If yes, attempt to match the local repository to a remote repository
        remote_repo = git_operations.match_local_repo_to_remote_repo(project_path, github_username, github_token)
        if remote_repo:
            # If a match is found, commence autosaving
            autosave(project_path, openai_key, bypass_check)
        else:
            # If no match is found, create and initialize a new repository (no remote repo, but local repo exists)
            git_operations.create_and_initialize_remote_repo(project_path, github_username, github_token)
    else:
        # If no, attempt to match the local directory to a remote repository
        remote_repo = git_operations.match_local_dir_to_remote_repo(project_path, github_username, github_token)
        if remote_repo:
            # If a match is found, we'll need to reconcile the contents of the local directory with the remote repository
            if git_operations.reconcile_local_dir_and_remote_repo(project_path, remote_repo, github_username, github_token):
                autosave(project_path, openai_key, bypass_check)
        else:
            # If no match is found, create and initialize a new repository (no remote repo, no local repo)
            git_operations.create_and_initialize_local_repo(project_path, github_username, github_token)
            git_operations.create_and_initialize_remote_repo(project_path, github_username, github_token)

def main():
    """Main function to load config and process all projects or a specific project."""
    try:
        config = load_config()
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    projects_dir = config['projects_dir']
    github_username = config['github_username']
    github_token = config['github_token']
    openai_key = config.get('openai_key', '')

    projects = []
    bypass_check = False
    if '--bypass-check' in sys.argv:
        bypass_check = True
        sys.argv.remove('--bypass-check')

    if len(sys.argv) > 1:
        projects = sys.argv[1:]
    else:
        projects = os.listdir(projects_dir)

    for project in projects:
        project_path = os.path.join(projects_dir, project)
        if os.path.isdir(project_path):
            logging.info(f"Processing project: {project}")
            try:
                process_project(project_path, github_username, github_token, openai_key, bypass_check)
            except Exception as e:
                logging.error(f"Error processing project {project}: {e}")
        else:
            logging.error(f"Project directory {project_path} does not exist.")

if __name__ == "__main__":
    main()