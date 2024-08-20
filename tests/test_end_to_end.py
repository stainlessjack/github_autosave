import sys
import os
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import process_project

@pytest.fixture
def mock_git_operations():
    with patch('main.git_operations') as mock:
        yield mock

@pytest.fixture
def mock_autosave():
    with patch('main.autosave') as mock:
        yield mock

def test_process_project_git_repo_with_remote(mock_git_operations, mock_autosave):
    mock_git_operations.is_git_repo.return_value = True
    mock_git_operations.match_local_repo_to_remote_repo.return_value = True

    process_project("dummy_path", "dummy_user", "dummy_token", "dummy_key")

    mock_autosave.assert_called_once_with("dummy_path", "dummy_key", False)

def test_process_project_git_repo_without_remote(mock_git_operations):
    mock_git_operations.is_git_repo.return_value = True
    mock_git_operations.match_local_repo_to_remote_repo.return_value = False

    process_project("dummy_path", "dummy_user", "dummy_token", "dummy_key")

    mock_git_operations.create_and_initialize_remote_repo.assert_called_once_with("dummy_path", "dummy_user", "dummy_token")

def test_process_project_non_git_repo_with_remote(mock_git_operations, mock_autosave):
    mock_git_operations.is_git_repo.return_value = False
    mock_git_operations.match_local_dir_to_remote_repo.return_value = True
    mock_git_operations.reconcile_local_dir_and_remote_repo.return_value = True

    process_project("dummy_path", "dummy_user", "dummy_token", "dummy_key")

    mock_autosave.assert_called_once_with("dummy_path", "dummy_key", False)

def test_process_project_non_git_repo_without_remote(mock_git_operations):
    mock_git_operations.is_git_repo.return_value = False
    mock_git_operations.match_local_dir_to_remote_repo.return_value = False

    process_project("dummy_path", "dummy_user", "dummy_token", "dummy_key")

    mock_git_operations.create_and_initialize_local_repo.assert_called_once_with("dummy_path", "dummy_user", "dummy_token")
    mock_git_operations.create_and_initialize_remote_repo.assert_called_once_with("dummy_path", "dummy_user", "dummy_token")