import json
import os
import time
import requests.exceptions
from tqdm import tqdm
from github import Github
from credentials import GITHUB_TOKEN, root_path

g1 = Github(GITHUB_TOKEN)

while True:
    choice0 = input("Choose one:\n1. Organisation's repo\n2. User's repo\n -------->your input:")
    if choice0 == '1':
        orgInput = input('Enter the org name:')
        org = g1.get_organization(orgInput)
        repos = org.get_repos()
        choice1 = int(input(
            f'I need :\n1. a single repo from {orgInput}\n2. all repos from {orgInput}\n3. a list of all repo\n -------->your input:'))
        if choice1 == 3:
            for repo in repos:
                print(repo.name)
            print('--------------')
            continue
        break
    elif choice0 == '2':
        orgInput = input('Enter the username(repo owner):')
        repos = g1.get_user(orgInput).get_repos()
        choice1 = int(input(
            f'I need :\n1. a single repo from {orgInput}\n2. all repos from {orgInput}\n3. a list of all repo\n -------->your input:'))
        if choice1 == 3:
            for repo in repos:
                print(repo.name)
            print('--------------')
            continue
        break

if choice1 == 1:
    repoInp = input('Enter the repo name:')
    repos = [repo for repo in repos if repo.name.lower() == repoInp.lower()]
if not repos:
    print('not found')
    quit()
repo_data = {}
issues_data = {}
pr_data = {}
for repo in repos:
    print(f'loading ---{repo.name}---...')
    repo_data[repo.name] = repo.raw_data
    issues = repo.get_issues(state='all')
    issues_number_list = []
    timelineis = {}
    print('\ngetting issues and pulls...')
    for issue in tqdm(issues):
        # issue_events = issue.get_events()
        try:
            timelineis[issue.number] = [issue.raw_data] + [events.raw_data for events in issue.get_timeline()]
        except requests.exceptions.ReadTimeout:
            print('timeout error.. retrying!!')
            time.sleep(5)
            timelineis[issue.number] = [issue.raw_data] + [events.raw_data for events in issue.get_timeline()]
        issues_number_list.append(issue.number)
    pulls = repo.get_pulls(state='all')
    pulls_numbers_list = []
    timelinepr = {}
    for pull in pulls:
        pulls_numbers_list.append(pull.number)
    issues_number_list.append(timelineis)
    issues_data[repo.name] = issues_number_list
    pr_data[repo.name] = pulls_numbers_list

response = ''

try:
    os.mkdir(os.path.join(root_path, orgInput.lower()))  # org folder creation
    root_path = root_path + '\\' + orgInput.lower()
    folders = [reponame for reponame in repo_data.keys()]
    for folder in folders:
        os.mkdir(os.path.join(root_path, folder))  # repo folder creation
        os.mkdir(os.path.join(root_path + '\\' + folder, 'issues'))  # issues folder creation
        os.mkdir(os.path.join(root_path + '\\' + folder, 'pr'))  # PR folder creation
except FileExistsError:
    print("org dir already exists. Please delete the prev dir, or move it to somewhere else")
    quit()

    ''' shutil rmtree could be potentially risky.
    Especially if mistake was made by client in giving the root path
    so commented it out'''
    # response = input(f'File Already exists. Do you want to overwrite {orgInput.lower()}?(y/n)').lower()
    # if response == 'y':
    #     shutil.rmtree(root_path + '\\' + orgInput.lower())
    # elif response == 'n':
    #     print('-----aborted-----')
    #     quit()

# write repo meta data & create pr+issues folder

for reponame in tqdm(repo_data.keys()):
    write_path = '\\'.join([root_path, reponame])
    with open(write_path + '\\repo_meta_data.json', 'w') as f:
        json.dump(repo_data[reponame], f)
    for issue in issues_data[reponame][:-1]:
        os.mkdir(os.path.join(write_path + '\\issues', str(issue)))
    for pr in pr_data[reponame]:
        os.mkdir(os.path.join(write_path + '\\pr', str(pr)))
    isdata = issues_data[reponame][-1]

    # issues events

    for issuenumber, dataset in isdata.items():
        if dataset:
            for event in dataset:
                state = ''
                if 'event' in event.keys():
                    eventName = event['event']
                else:
                    eventName = 'started'
                    state = '(' + event['state'] + ')'
                if 'user' in event.keys():
                    username = event["user"]["login"]
                    date = event['created_at'].replace(":", "-") if 'created_at' in event.keys() else event[
                        'submitted_at'].replace(":", "-")
                elif 'actor' in event.keys():
                    if 'login' in event['actor']:
                        username = event["actor"]["login"]
                    else:
                        username = 'None'
                    date = event['created_at'].replace(":", "-") if 'created_at' in event.keys() else event[
                        'submitted_at'].replace(":", "-")
                else:
                    username = event['author']['name']
                    date = event['author']['date'].replace(":", "-")
                with open(write_path + '\\issues' + f'\\{issuenumber}\\{state}{date}-{eventName}-by-{username}.json',
                          'w') as f:
                    json.dump(event, f)
                # write pr
                if issuenumber in pr_data[reponame]:
                    with open(write_path + '\\pr' + f'\\{issuenumber}\\{state}{date}-{eventName}-by-{username}.json',
                              'w') as f:
                        json.dump(event, f)
