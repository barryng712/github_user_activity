import sys
import requests
import json
import os
from datetime import datetime, timedelta
from tabulate import tabulate

CACHE_FILE = "github_activity_cache.json"
CACHE_EXPIRY = timedelta(hours=1)

def format_date(date_string):
    date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    return date.strftime("%Y-%m-%d %H:%M:%S")

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def fetch_recent_activity(github_username, days=30, max_events=100):
    cache = load_cache()
    cache_key = f"{github_username}_{days}_{max_events}"
    if cache_key in cache:
        cached_time = datetime.fromisoformat(cache[cache_key]["time"])
        if datetime.now() - cached_time < CACHE_EXPIRY:
            return cache[cache_key]["data"]
    # fetch the recent activity from the GitHub API
    api_url = f"https://api.github.com/users/{github_username}/events"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    params = {'per_page': 100}  # Maximum allowed per page
    all_activities = []
    try:
        while len(all_activities) < max_events:
            response = requests.get(api_url, headers=headers, params=params)
            response.raise_for_status() # raise an exception for bad status codes
            activities = response.json()
            if not activities:
                break
            for activity in activities:
                activity_date = datetime.strptime(activity.get("created_at"), "%Y-%m-%dT%H:%M:%SZ")
                if datetime.now() - activity_date > timedelta(days=days):
                    cache[cache_key] = {
                        "time": datetime.now().isoformat(),
                        "data": all_activities
                    }
                    save_cache(cache)
                    return all_activities
                all_activities.append(activity)

                if len(all_activities) >= max_events:
                    cache[cache_key] = {
                        "time": datetime.now().isoformat(),
                        "data": all_activities
                    }
                    save_cache(cache)
                    return all_activities
            if 'next' in response.links:
                api_url = response.links['next']['url']
            else:
                break
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"User '{github_username}' not found.")
        elif e.response.status_code == 403:
            print(f"API rate limit exceeded. Please try again later.")
        else:
            print(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the data: {e}")
    
    cache[cache_key] = {
        "time": datetime.now().isoformat(),
        "data": all_activities
    }
    save_cache(cache)
    return all_activities

def display_activity(activities):
    if not activities:
        print("No recent activity found for this user.")
        return
    
    print(f"Displaying {len(activities)} most recent activities:")
    print(f"Earliest activity: {format_date(activities[-1]['created_at'])}")
    print(f"Latest activity: {format_date(activities[0]['created_at'])}")
    print("---")

    table_data = []
    for activity in activities:
        event_type = activity.get("type")
        repo_name = activity.get("repo").get("name")
        created_at = format_date(activity.get("created_at"))
        payload = activity.get("payload", {})
        details = event_type
        if event_type == "PushEvent":
            commits = payload.get('commits', [])
            details = f"Pushed {len(commits)} commit(s)"
        elif event_type == "IssuesEvent":
            action = payload.get('action')
            issue_number = payload.get('issue', {}).get('number')
            details = f"{action.capitalize()} issue #{issue_number}"
        elif event_type == "PullRequestEvent":
            action = payload.get('action')
            pr_number = payload.get('pull_request', {}).get('number')
            details = f"{action.capitalize()} PR #{pr_number}"
        elif event_type in ["CreateEvent", "DeleteEvent"]:
            ref_type = payload.get('ref_type')
            action = "Created" if event_type == "CreateEvent" else "Deleted"
            details = f"{action} {ref_type}"
        table_data.append([details, repo_name, created_at])
    
    headers = ["Event", "Repository", "Date"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def filter_activities(activities, event_type):
    return [activity for activity in activities if activity.get("type") == event_type]

def fetch_user_info(github_username):
    api_url = f"https://api.github.com/users/{github_username}"
    response = requests.get(api_url)
    return response.json() if response.status_code == 200 else None

def display_user_info(user_info):
    if user_info:
        print(f"User: {user_info['login']}")
        print(f"Name: {user_info['name']}")
        print(f"Bio: {user_info['bio']}")
        print(f"Public Repos: {user_info['public_repos']}")
        print(f"Followers: {user_info['followers']}")
        print(f"Following: {user_info['following']}")
    else:
        print("Unable to fetch user information.")

def fetch_repo_stats(github_username):
    api_url = f"https://api.github.com/users/{github_username}/repos"
    response = requests.get(api_url)
    if response.status_code == 200:
        repos = response.json()
        return {
            'total_repos': len(repos),
            'total_stars': sum(repo['stargazers_count'] for repo in repos),
            'total_forks': sum(repo['forks_count'] for repo in repos),
            'languages': set(repo['language'] for repo in repos if repo['language'])
        }
    return None

def display_repo_stats(stats):
    if stats:
        print(f"Total Repositories: {stats['total_repos']}")
        print(f"Total Stars: {stats['total_stars']}")
        print(f"Total Forks: {stats['total_forks']}")
        print(f"Languages Used: {', '.join(stats['languages'])}")
    else:
        print("Unable to fetch repository statistics.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py <github_username> [days_to_fetch] [max_events] [event_filter]")
        sys.exit(1)
    
    github_username = sys.argv[1]
    
    # Parse optional arguments
    args = sys.argv[2:]
    days_to_fetch = 30
    max_events = 100
    event_filter = None

    for arg in args:
        if arg.isdigit():
            if days_to_fetch == 30:
                days_to_fetch = int(arg)
            elif max_events == 100:
                max_events = int(arg)
        else:
            event_filter = arg

    # Fetch and display user info
    user_info = fetch_user_info(github_username)
    display_user_info(user_info)
    print("\n")

    # Fetch and display repo stats
    repo_stats = fetch_repo_stats(github_username)
    display_repo_stats(repo_stats)
    print("\n")

    # Fetch and display activities
    activities = fetch_recent_activity(github_username, days_to_fetch, max_events)
    if event_filter:
        activities = filter_activities(activities, event_filter)
    
    if activities:
        display_activity(activities)
    else:
        print("No recent activity found for this user.")

if __name__ == "__main__":
    main()