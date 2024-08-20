# Github Autosave

## Overview

Hourly checks to make sure changes to your project never goes more than a day without being saved remotely.

## Features

- **Automatic Git Staging, Committing, and Pushing:** The script automatically stages, commits, and pushes any changes in your project's directory to the remote repository as a new timestamped branch.
- **Timestamped Branches and Commits:** Each commit is timestamped with the current date and time, and a new branch is created so you can easily track changes over time.
- **New Project Setup:** When new projects are detected, the script will initialize a new repository and make the first commit.
- **Easy Setup:** Just point the script to your Project directory and provide you Git credentials, and you're good to go!
- **AI Branch Naming and Commit Messages:** Given an OpenAI API key, the script can also generate branch names and commit messages based on the changes made to your project.
- **OS Agnostic:** Works on Windows, macOS, and Linux.

## Requirements

- **Git** installed on your system.
- **Python 3** installed on your system.
- **Project Directory** where your project files are located.
- **Git Credentials** (username and password) for pushing changes to the remote repository.
- **OpenAI API Key** (optional) for AI-generated branch names and commit messages.

## Installation

1. Clone this repository to your local machine.
2. Install pipenv if you don't have it already: `pip install pipenv`
3. From the github-autosave directory, run `pipenv install` to install the required dependencies.
4. Run setup with `pipenv run python setup.py`.
5. Follow the prompts to set up your project directory, Git credentials, and OpenAI API key (if desired).
