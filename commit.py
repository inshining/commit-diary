import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

"""
Get this week's commit message that user pushed to.
"""

load_dotenv()
token = os.getenv('GITHUB_TOKEN')
username = os.getenv("USERNAME")

def get_current_week_range():
    """Returns the start and end datetime of the current week."""
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday
    return start_of_week, end_of_week

def get_repos_committed(username, token, since):
    """Fetch Repos that have committed by the user since the specified date."""
    url = "https://api.github.com/search/commits"
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.cloak-preview'
    }
    params = {
        'q': f'author:{username} committer-date:>{since}',
        'sort': 'committer-date',
        'order': 'desc',
        'per_page': 100
    }

    commit_repos = set()
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch commits: {response.json()}")
            break

        commits = response.json().get('items', [])
        for commit in commits:
            repo_full_name = commit['repository']['full_name']
            commit_repos.add(repo_full_name)

        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            break

    return list(commit_repos)

def get_default_branch(repo_full_name, token):
    """Fetch the default branch for the specified repository."""
    url = f"https://api.github.com/repos/{repo_full_name}"
    headers = {
        'Authorization': f'token {token}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        repo_info = response.json()
        return repo_info['default_branch']
    else:
        print(f"Failed to fetch repository info for {repo_full_name}: {response.json()}")
        return None

def get_commit_messages(repo_full_name, branch='main', token=None, since=None, until=None):
    """Fetch commit messages from the specified repository within the date range."""
    
    default_branch = get_default_branch(repo_full_name, token)
    if not default_branch:
        print(f"Could not determine default branch for {repo_full_name}. Skipping.")
        return []

    branch = default_branch if branch != default_branch else branch
    
    url = f"https://api.github.com/repos/{repo_full_name}/commits"
    
    
    params = {
        'sha': branch,
        'per_page': 50,  
        'since': since,
        'until': until
    }

    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'

    commit_messages = []
    while url:
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"Failed to fetch commits for {repo_full_name}: {response.json()}")
            break
        
        commits = response.json()
        commit_messages.extend(commit['commit']['message'] for commit in commits)

        
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            break

    return commit_messages

def get_iso_date(date_time):
    """Returns ISO FORMAT + Z from datetime"""
    return date_time.isoformat() + 'Z'


start_of_week, end_of_week = get_current_week_range()
since_date = get_iso_date(start_of_week)
until_date = get_iso_date(end_of_week)

repositories = get_repos_committed(username, token, since_date)

if not repositories:
    print("No repositories found with commits this week.")
else:
    for repo in repositories:
        print(f"Repository: {repo}")
        commit_messages = get_commit_messages(repo, token=token, since=since_date, until=until_date)
        if commit_messages:
            print(commit_messages)
        else:
            print("No commit messages found or failed to fetch commit messages.")



