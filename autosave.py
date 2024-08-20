import datetime
import os
import logging
from git import Repo, GitCommandError

from utils import generate_ai_message

# bypass_check is used to bypass the check for changes and run the autosave anyway
def autosave(project_path, openai_key, bypass_check=False):
    """Autosave the project to the remote repository"""
    logging.info(f"Starting autosave for project: {project_path}")

    try:
        repo = Repo(project_path)
        current_branch = repo.active_branch
        current_branch_name = current_branch.name
        now = datetime.datetime.now()

        # Decide if an autosave is necessary
        changes = get_changes(repo, now)
        if not changes and not bypass_check:
            logging.info("No local changes older than 24 hours.")
            return

        # Stash changes before switching branches
        repo.git.stash('--include-untracked')

        # Push up any untracked branches besides the current branch
        push_untracked_branches(repo, current_branch_name)

        # Find the branch to branch off of
        common_ancestor = find_common_ancestor(repo, current_branch)
        if not common_ancestor:
            logging.error("No common ancestor found with any remote branch.")
            return

        # Push the current branch to the remote repository
        repo.remotes.origin.push(current_branch_name)

        # Create the autosave branch, add and commit the changes, and push the autosave branch to the remote repository
        autosave_branch_name = create_autosave_branch(repo, current_branch_name, common_ancestor, now)
        
        # Apply the stashed changes to the new autosave branch
        try:
            repo.git.stash('apply')
        except GitCommandError as e:
            logging.error(f"Git command error during stash apply: {e}")

        if repo.is_dirty(untracked_files=True):
            repo.git.add(A=True)
            commit_message = generate_ai_message(repo.git.diff('HEAD', '--staged'), openai_key)
            repo.index.commit(commit_message)
            repo.remotes.origin.push(autosave_branch_name)
        logging.info(f"Autosaved changes to branch {autosave_branch_name} for project {project_path}")
    except GitCommandError as e:
        logging.error(f"Git command error during autosave for project {project_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error during autosave for project {project_path}: {e}")
    finally:
        repo.git.checkout(current_branch_name)
        try:
            repo.git.stash('pop')
        except GitCommandError as e:
            logging.error(f"Git command error during stash pop: {e}")

def get_changes(repo, now):
    changes = []
    for item in repo.index.diff(None):
        path = os.path.join(repo.working_dir, item.a_path)
        change_time = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        if (now - change_time).days >= 1:
            changes.append(item.a_path)
    return changes

def find_common_ancestor(repo, current_branch):
    remote_branches = repo.remotes.origin.refs
    for remote_branch in remote_branches:
        try:
            return repo.merge_base(current_branch, remote_branch)[0]
        except IndexError:
            continue
    return None

def create_autosave_branch(repo, current_branch_name, common_ancestor, now):
    increment = 0
    base_autosave_branch_name = f"{current_branch_name}_{now.strftime('%Y%m%d')}_autosave_{increment}"
    autosave_branch_name = base_autosave_branch_name

    # Check if the branch already exists and increment the name if necessary
    while autosave_branch_name in repo.branches:
        increment += 1
        autosave_branch_name = f"{base_autosave_branch_name}_{increment}"

    repo.git.checkout(common_ancestor)
    repo.git.checkout('-b', autosave_branch_name)
    return autosave_branch_name

def push_untracked_branches(repo, current_branch_name):
    # Push up any untracked branches besides the current branch (ignore branches with autosave in the name)
    for branch in repo.branches:
        if branch.tracking_branch() is None and branch.name != current_branch_name and "autosave" not in branch.name:
            repo.git.checkout(branch)
            repo.remotes.origin.push(branch)
    repo.git.checkout(current_branch_name)