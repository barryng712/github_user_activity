import requests
import sys 
from datetime import datetime

def format_date(date_string):
    date = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    return date.strftime("%Y-%m-%d %H:%M:%S")

def fetch_recent_activity(github_username):
    api_url = f"https://api.github.com/users/{github_username}/events"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

def display_activity(activities):
    if not activities:
        print("No recent activity found for this user.")
        return
    
    print("Recent GitHub Activity:")
    for activity in activities:
        event_type = activity.get("type")
        repo_name = activity.get("repo").get("name")
        created_at = format_date(activity.get("created_at"))
        
        if event_type == "PushEvent":
            commits = len(activity["payload"]["commits"])
            print(f"🔨 Pushed {commits} commit{'s' if commits > 1 else ''} to {repo_name} on {created_at}")
        elif event_type == "PullRequestEvent":
            action = activity["payload"]["action"]
            pr_number = activity["payload"]["number"]
            print(f"🔀 Pull request #{pr_number} {action} on {repo_name} on {created_at}")
        elif event_type == "IssuesEvent":
            action = activity["payload"]["action"]
            issue_number = activity["payload"]["issue"]["number"]
            print(f"📝 Issue #{issue_number} {action} on {repo_name} on {created_at}")
        elif event_type == "IssueCommentEvent":
            issue_number = activity["payload"]["issue"]["number"]
            print(f"💬 Commented on issue #{issue_number} in {repo_name} on {created_at}")
        else:
            print(f"➡️ {event_type} on {repo_name} on {created_at}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py <github_username>")
        sys.exit(1)
    github_username = sys.argv[1]
    activities = fetch_recent_activity(github_username)
    display_activity(activities)

if __name__ == "__main__":
    main()