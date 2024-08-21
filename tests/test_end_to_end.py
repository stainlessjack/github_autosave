import pytest

# Test 1: dir is not a git repo and there is no remote repo with the same name
# Expected Result: create and initialize local and remote repos

# Test 2: dir is not a git repo and there is a remote repo with the same name
# Expected Result: create and initialize local, contents of the dir are pushed as a new branch in the remote repo

# Test 3: dir is a git repo and there is no remote repo with the same name
# Expected Result: create and initialize remote repo, contents of the dir are pushed as a new branch in the remote repo

# Test 4: dir is a git repo and there is a remote repo with the same name
# Test 4a: the repos have common commits
# Expected Result: contents of the dir are pushed as a new branch in the remote repo

# Test 4b: the repos have no common commits
# Expected Result: contents of the dir are moved to a new dir named dir_2 and a new remote repo is created based on the local repo,
# which is now dir_2