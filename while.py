import os
from git import Repo

def push_to_github(repo_path, commit_message, access_token, branch_name):
    # Create a GitPython Repo object for the specified repository path
    repo = Repo(repo_path)

    # Add all changes to the staging area
    repo.index.add("*")

    # Create a new commit with the specified commit message
    repo.index.commit(commit_message)

    # Switch to the specified branch (or create it if it doesn't exist)
    try:
        repo.heads[branch_name].checkout()
    except IndexError:
        repo.create_head(branch_name)
        repo.heads[branch_name].checkout()

    # Push changes to the remote repository using the provided personal access token
    remote_origin = repo.remote(name="origin")
    remote_url = remote_origin.url
    remote_url_with_token = remote_url.replace("https://", f"https://{access_token}@")
    remote_origin.set_url(remote_url_with_token)
    remote_origin.push(refspec=f"refs/heads/{branch_name}")


repo_path = "."
commit_message = "Commit message"
access_token = os.getenv("token")
branch_name = "modify-scripts"
push_to_github(repo_path, commit_message, access_token, branch_name)

