import os
import git
import logging
import requests
from git.exc import GitCommandError
from git import Repo
import shutil

def is_git_repo(path):
    """Check if the given path is a git repository."""
    logging.debug(f"Checking if the path {path} is a git repository.")
    try:
        _ = git.Repo(path).git_dir
        logging.debug(f"The path {path} is a git repository.")
        return True
    except git.exc.InvalidGitRepositoryError:
        logging.debug(f"The path {path} is not a git repository.")
        return False

def match_local_repo_to_remote_repo(path, github_username, github_token):
    """Match a local git repository to a remote GitHub repository."""
    logging.debug(f"Attempting to match local repository at {path} to a remote repository.")
    try:
        repo = Repo(path)
        if 'origin' not in repo.remotes:
            logging.debug(f"No remote named 'origin' found in the repository at {path}.")
            return None

        remote_url = repo.remotes.origin.url
        logging.debug(f"Found remote URL: {remote_url}")
        if 'github.com' not in remote_url:
            logging.debug(f"Remote URL {remote_url} is not a GitHub repository.")
            return None

        logging.debug(f"Remote URL {remote_url} is a GitHub repository.")
        repo_name = remote_url.split('github.com/')[1].rstrip('.git')
        url = f"https://api.github.com/repos/{repo_name}"
        headers = {'Authorization': f'token {github_token}'}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logging.debug(f"Remote repository {remote_url} does not exist on GitHub.")
            return None

        logging.debug(f"Remote repository {remote_url} exists on GitHub.")
        origin = repo.remotes.origin
        origin.fetch()

        remote_branches = origin.refs
        if not remote_branches:
            logging.debug(f"No remote branches found for {remote_url}")
            return None

        for remote_branch in remote_branches:
            try:
                remote_commits = set(repo.git.rev_list(remote_branch.name).split())
                local_commits = set(repo.git.rev_list('HEAD').split())
                if remote_commits & local_commits:
                    logging.debug(f"Local and remote repositories share common commits.")
                    return remote_url
            except GitCommandError as e:
                logging.debug(f"Error checking commits for branch {remote_branch.name}: {e}")
                continue

        logging.debug(f"No common commits found. Renaming local repository and pushing it up.")
        base_repo_name = os.path.basename(path)
        increment = 2
        new_repo_name = f"{base_repo_name}_{increment}"

        while True:
            url = f"https://api.github.com/repos/{github_username}/{new_repo_name}"
            response = requests.get(url, headers=headers)
            if response.status_code == 404:
                break
            increment += 1
            new_repo_name = f"{base_repo_name}_{increment}"

        new_path = os.path.join(os.path.dirname(path), new_repo_name)
        os.rename(path, new_path)
        repo = Repo(new_path)
        repo.create_remote('origin', f"https://github.com/{github_username}/{new_repo_name}.git")
        repo.remotes.origin.push(repo.head.ref)
        logging.debug(f"Renamed local repository to {new_repo_name} and pushed to remote.")
        return f"https://github.com/{github_username}/{new_repo_name}.git"
    except Exception as e:
        logging.debug(f"Failed to match local repository to remote repository: {e}")
        return None

def match_local_dir_to_remote_repo(path, github_username, github_token):
    """Match a local directory to a remote GitHub repository based on name."""
    dir_name = os.path.basename(path)
    logging.debug(f"Attempting to match local directory {dir_name} to a remote repository.")
    url = f"https://api.github.com/user/repos"
    headers = {'Authorization': f'token {github_token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.debug(f"Successfully fetched repositories for user {github_username}.")
        repos = response.json()
        for repo in repos:
            if repo['name'].lower() == dir_name.lower():
                logging.debug(f"Found matching repository: {repo['html_url']}")
                return repo['html_url']
    logging.debug(f"No matching repository found for directory {dir_name}.")
    return None

def create_and_initialize_local_repo(path, github_username, github_token):
    """Create a new local GitHub repository, local repo does not exist."""
    logging.debug(f"Creating and initializing a new local repository at {path}.")
    try:
        repo = Repo.init(path)
        repo.git.add(A=True)  # Add all files to the repository
        repo.index.commit("Initial commit")
        logging.debug(f"Initialized a new local repository at {path}.")
    except GitCommandError as e:
        logging.error(f"Failed to create and initialize local repository at {path}: {e}")
        raise

def create_and_initialize_remote_repo(path, github_username, github_token):
    """Create a new remote GitHub repository, local repo already exists."""
    logging.debug(f"Creating and initializing a new remote repository for local repo at {path}.")
    try:
        base_repo_name = os.path.basename(path)
        repo_name = base_repo_name
        url = f"https://api.github.com/user/repos"
        headers = {'Authorization': f'token {github_token}'}
        data = {'name': repo_name, 'private': False}
        response = requests.post(url, headers=headers, json=data)
        
        increment = 1
        while response.status_code == 422 and 'name already exists on this account' in response.text:
            increment += 1
            repo_name = f"{base_repo_name}_{increment}"
            data['name'] = repo_name
            response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 201:
            logging.error(f"Failed to create remote repository: {response.json()}")
            raise Exception(f"Failed to create remote repository: {response.json()}")

        remote_url = response.json()['clone_url']
        repo = Repo(path)
        
        if not repo.head.is_valid():
            repo.git.add(A=True)
            repo.index.commit("Initial commit")
        
        if 'origin' in repo.remotes:
            logging.debug(f"Remote 'origin' already exists. Updating URL to {remote_url}.")
            repo.remotes.origin.set_url(remote_url)
            origin = repo.remotes.origin
        else:
            origin = repo.create_remote('origin', remote_url)
        origin.push(repo.head.ref)
        logging.debug(f"Created and pushed to new remote repository {remote_url} for local repo at {path}.")
    except Exception as e:
        logging.error(f"Failed to create and initialize remote repository for local repo at {path}: {e}")
        raise

def reconcile_local_dir_and_remote_repo(path, remote_url, github_username, github_token):
    """Reconcile the contents of a local directory with a remote repository."""
    logging.debug(f"Reconciling local directory {path} with remote repository.")

    try:
        temp_dir = os.path.join(os.path.dirname(path), 'temp')
        
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        shutil.copytree(path, temp_dir)
        shutil.rmtree(path)
        Repo.clone_from(remote_url, path)
        shutil.copytree(temp_dir, path, dirs_exist_ok=True)
        shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        logging.error(f"Failed to reconcile local directory with remote repository: {e}")
        return False