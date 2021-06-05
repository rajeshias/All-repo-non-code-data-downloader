import json
import os
import github.GithubException
from github import Github
from credentials import GITHUB_TOKEN, root_path

g1 = Github(GITHUB_TOKEN)


def create_new_folder(output_path, folder_name):
    """It creates a new folder inside a path, ignores if already exists"""
    if not output_path:
        output_path = os.getcwd()
    if not os.path.exists(os.path.join(output_path, folder_name)):
        os.mkdir(os.path.join(output_path, folder_name))


def write_data(destination, file):
    with open(destination, 'w') as jsonFile:
        json.dump(file, jsonFile)


repos = []
name = ''

#  User-menu
while True:
    choice0 = input("Choose one:\n1. Organisation's repo\n2. User's repo\n -------->your input:")
    try:
        if choice0 == '1':
            name = input('Enter the org name:').lower()
            repos = g1.get_organization(name).get_repos()
        elif choice0 == '2':
            name = input('Enter user name:').lower()
            repos = g1.get_user(name).get_repos()
        elif choice0.lower() == 'exit':
            quit()
        else:
            print('not a valid input. Please reply with 1 or 2 or exit')
            continue
    except github.BadCredentialsException:
        print("Github token in credentials.py is not valid! You can get one here: https://github.com/settings/tokens")
        quit()
    except github.UnknownObjectException:
        print("----\nNo org/user found! Kindly check your spelling! \n----")
        continue
    break

if not repos:
    print('No Public Repositories found')
    quit()

create_new_folder(root_path, name)

repo_data = {}
issues_data = {}
pr_data = {}
for i, repo in enumerate(repos):
    print(f'loading ---{repo.name}---({i + 1}/{repos.totalCount})')
    create_new_folder(os.path.join(root_path, name), repo.name)
    print("getting repo data...")
    write_data(os.path.join(root_path, name, repo.name, 'repo_meta_data.json'), repo.raw_data)
    issues = repo.get_issues(state='all')
    issues_number_list = []
    timelineis = {}
    print('getting issues and pulls...')
    create_new_folder(os.path.join(root_path, name, repo.name), 'issues')
    create_new_folder(os.path.join(root_path, name, repo.name), 'pr')
    for issue in issues:
        number_plus_state = str(issue.number) if issue.state == 'closed' else str(issue.number) + '(open)'
        print(number_plus_state)
        create_new_folder(os.path.join(root_path, name, repo.name, 'issues'), number_plus_state)
        write_data(os.path.join(root_path, name, repo.name, 'issues', number_plus_state,
                                f'{issue.raw_data["created_at"].replace(":", "-")}-created-by-{issue.raw_data["user"]["login"]}.json'),
                   issue.raw_data)
        prList = [pull.number for pull in repo.get_pulls(state='all')]
        for pull in prList:
            create_new_folder(os.path.join(root_path, name, repo.name, 'pr'), str(pull))
        for events in issue.get_timeline():
            event = events.raw_data
            if 'user' in event.keys():
                userName = event["user"]["login"]
                date = event['created_at'].replace(":", "-") if 'created_at' in event.keys() else event[
                    'submitted_at'].replace(":", "-")
            elif 'actor' in event.keys():
                if 'login' in event['actor']:
                    userName = event["actor"]["login"]
                else:
                    userName = 'None'
                date = event['created_at'].replace(":", "-") if 'created_at' in event.keys() else event[
                    'submitted_at'].replace(":", "-")
            else:
                userName = event['author']['name']
                date = event['author']['date'].replace(":", "-")

            write_data(os.path.join(root_path, name, repo.name, 'issues', number_plus_state,
                                    f'{date}-{event["event"]}-by-{userName}.json'),
                       issue.raw_data)
            if issue.number in prList:
                write_data(os.path.join(root_path, name, repo.name, 'pr', str(issue.number),
                                        f'{date}-{event["event"]}-by-{userName}.json'),
                           issue.raw_data)
