import sys
import requests
from datetime import datetime
def fetch_recent_activity(github_username):
    # fetch the recent activity from the GitHub API
    api_url = f"https://api.github.com/users/{github_username}/events"
    try:
        response = requests.get(api_url)
        response.raise_for_status() # raise an exception for bad status codes
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"User '{github_username}' not found.")
        elif e.response.status_code == 403:
            print(f"API rate limit exceeded. Please try again later.")
        else:
            print(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the data: {e}")
    return None

def format_date(created_at):
    date = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    return date.strftime("%Y-%m-%d %H:%M:%S")

def display_activity(activities):
    for activity in activities:
        event_type = activity.get("type")
        repo_name = activity.get("repo").get("name")
        created_at = format_date(activity.get("created_at"))
        payload = activity.get("payload", {})
        if event_type == "PushEvent":
            commits = payload.get("commits", [])
            print(f"Pushed {len(commits)} commit(s) to {repo_name} at {created_at}")
        elif event_type == "IssuesEvent":
            action = payload.get("action")
            issue_number = payload.get("issue", {}).get("number")
            print(f"{action.capitalize()} issue #{issue_number} in {repo_name} at {created_at}")
        elif event_type == "WatchEvent":
            print(f"Starred {repo_name} at {created_at}")
        elif event_type == "CreateEvent":
            ref_type = payload.get("ref_type")
            print(f"Created {ref_type} in {repo_name} at {created_at}")
        elif event_type == "DeleteEvent":
            ref_type = payload.get("ref_type")
            print(f"Deleted {ref_type} in {repo_name} at {created_at}")
        elif event_type == "PullRequestEvent":
            action = payload.get("action")
            pr_number = payload.get("pull_request", {}).get("number")
            print(f"{action.capitalize()} pull request #{pr_number} in {repo_name} at {created_at}")
        else:
            print(f"{event_type} in {repo_name} at {created_at}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python cli.py <github_username>")
        sys.exit(1)
    # get the github username from the command line arguments
    github_username = sys.argv[1]
    # fetch the recent activity from the GitHub API
    activities = fetch_recent_activity(github_username)

    if activities:
        display_activity(activities)
    else:
        print("No recent activity found for this user.")

if __name__ == "__main__":
    main()
