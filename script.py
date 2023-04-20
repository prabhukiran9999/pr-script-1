import subprocess
import os
import json
from subprocess import call
import time
from git import Repo
repo_path = "./"
# ATH_OF_GIT_REPO = r'.\.git' 
repo = Repo(repo_path)
subprocess.run(["ls", "-l", "/dev/null"], capture_output=True)

#Get GH Cli version
gh_version = call(["gh", "--version"])

# Token to use GH CLI
token = os.getenv("token")
# Execute the `gh auth login` command and provide your personal access token as input
subprocess.run(["gh", "auth", "login", "--with-token"], input=f"{token}\n", text=True)
# Execute project-set creation script
try :
    os.chdir('/bin')
    subprocess.call(['./project_set_admin.sh'])
except subprocess.CalledProcessError as e:
    print(e)
# Get the project-set name created
project_Set_info = subprocess.Popen(["git", "ls-files", "--others", "--directory", "--exclude-standard"],stdout=subprocess.PIPE).communicate()[0].decode("utf-8").rstrip()
checkout_branch_name = project_Set_info.strip("/")
print(checkout_branch_name)
#Create a new branch with the name of the project set created
checkout_branch = repo.git.checkout('-b', checkout_branch_name)
# Commit message for Push
COMMIT_MESSAGE = 'comment from python script'
def git_push():
    branch = checkout_branch_name
    repo = Repo('.')
    repo.git.add(all=True)
    repo.index.commit(COMMIT_MESSAGE)
    repo.git.push('origin', branch)
    
git_push()
time.sleep(5)
## Create Pull reequest and sleep for 5 min
create_pr = subprocess.Popen(["gh", "pr", "create", "-t created a new project set", "-b created a new project set using provisonor script", "-rsvalmiki1102"],stdout=subprocess.PIPE).communicate()[0] 
pr_url = create_pr.decode("utf-8").rstrip() 
print (f'Pull_request for new project-set({checkout_branch_name}) accounts created successfully')
#Sleep for 5 sec after pull request is created so the actions will register
time.sleep(5) #Sleep for 5 secs
print(pr_url)
# Check for pull request actions to complete
check_pr = json.loads(subprocess.Popen(["gh", "pr", "view", pr_url, "--json", "statusCheckRollup"],stdout=subprocess.PIPE).communicate()[0].decode("utf-8").rstrip())
print(check_pr)
workflow_id = str(json.loads(subprocess.Popen(["gh", "run", "list", "-b", checkout_branch_name, "-L", "1", "--json", "databaseId"],stdout=subprocess.PIPE).communicate()[0])[0]['databaseId'])
step = "account-creation"
# Function to get the pull request workflow status and merge the PR once the workflow status are successful
def pr_workflow_status(workflow_id,pr_url):
    workflow_status = ""
    while workflow_status != "completed":
        time.sleep(5)
        workflow_status = json.loads(subprocess.Popen(["gh", "run", "view", workflow_id, "--json", "status"],stdout=subprocess.PIPE).communicate()[0])['status']
        workflow_conclusion = json.loads(subprocess.Popen(["gh", "run", "view", workflow_id, "--json", "conclusion"],stdout=subprocess.PIPE).communicate()[0])['conclusion']
        if workflow_status =='queued':
            print(f'pull request workflow status for {step} is {workflow_status}')
            continue
        elif workflow_status == "in_progress":
            print(f'pull request workflow status for {step} is {workflow_status}')
            continue
        elif workflow_status == "completed" and workflow_conclusion == "success":
            print(f'pull request workflow status for {step} is {workflow_status} and the is {workflow_conclusion}')
            #Merge pull request when workflow is successful
            merge_pr = subprocess.call(["gh", "pr", "merge", pr_url, "--admin", "-m"])
            if merge_pr == 0:
                print(f"Pull request,{pr_url} merged successfully")
                time.sleep(5)
            else:
                print(f"problem merging a PR,{pr_url}")
            break
        elif workflow_status =="completed" and workflow_conclusion == "failure":
            print("Push workflow failed")
            break
# Function to get the Push workflow status
def push_workflow_status(push_workflow_id):
    push_workflow_status = ""
    while push_workflow_status != "completed":
        time.sleep(5)
        push_workflow_status = json.loads(subprocess.Popen(["gh", "run", "view", push_workflow_id, "--json", "status"],stdout=subprocess.PIPE).communicate()[0])['status']
        push_workflow_conclusion = json.loads(subprocess.Popen(["gh", "run", "view", workflow_id, "--json", "conclusion"],stdout=subprocess.PIPE).communicate()[0])['conclusion']
        if push_workflow_status =='queued':
            print(f'push workflow status for {step} is {push_workflow_status}')
            continue
        elif push_workflow_status == "in_progress":
            print(f'push workflow status for {step} is {push_workflow_status}')
            continue
        elif push_workflow_status == "completed" and push_workflow_conclusion == "success":
            print(f'push workflow status for {step} is {push_workflow_status}')
            return push_workflow_status
        elif push_workflow_status == "completed" and push_workflow_conclusion == "failure":
            print("Push workflow failed")
            return push_workflow_status
pr_workflow_status(workflow_id,pr_url)
time.sleep(5)
push_workflow_id = str(json.loads(subprocess.Popen(["gh", "run", "list", "-b", "main", "-L", "1", "--json", "databaseId"],stdout=subprocess.PIPE).communicate()[0])[0]['databaseId'])
push_status = push_workflow_status(push_workflow_id)
print(push_status)
# Create layers if push workflow status are succesfull
if push_status == "completed":
    try :
        layer_creation = subprocess.call(['./project_set_admin.sh'])
        if layer_creation == 0:
            print("layers created seccussfully") 
        else:
            print(f"problem creating pull request for layers")
    except subprocess.CalledProcessError as e:
        print(e)
else:
    print("Push workflow for accounts failed")
git_push()
step = "layer-creation"
layer_pr = subprocess.Popen(["gh", "pr", "create", "-t created a new project set", "-b created a new project set using provisonor script", "-rsvalmiki1102"],stdout=subprocess.PIPE).communicate()[0] 
pr_url = layer_pr.decode("utf-8").rstrip() 
print ('Pull_request for layers created successfully')
# #Sleep for 5 sec after pull request is created so the actions will register
time.sleep(5) #Sleep for 5 secs
print(pr_url)
workflow_id = str(json.loads(subprocess.Popen(["gh", "run", "list", "-b", checkout_branch_name, "-L", "1", "--json", "databaseId"],stdout=subprocess.PIPE).communicate()[0])[0]['databaseId'])
pr_workflow_status(workflow_id,pr_url)
time.sleep(5)
push_workflow_id = str(json.loads(subprocess.Popen(["gh", "run", "list", "-b", "main", "-L", "1", "--json", "databaseId"],stdout=subprocess.PIPE).communicate()[0])[0]['databaseId'])
push_status = push_workflow_status(push_workflow_id)
print(push_status)
#Checkout to main and  Delete the branch locally
subprocess.run(f"git checkout main", shell=True)
subprocess.run(f"git branch -D {checkout_branch_name}", shell=True)
# Delete the branch remotely
subprocess.run(f"git push origin --delete {checkout_branch_name}", shell=True)