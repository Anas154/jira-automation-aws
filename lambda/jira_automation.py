import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def make_request(url, method='GET', data=None, headers=None):
    """Make HTTP request"""
    if headers is None:
        headers = {}
    
    if data and isinstance(data, dict):
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')
            return status_code, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        log(f"Request error: {str(e)}")
        raise

def run_automation():
    """Main automation logic"""
    # Get environment variables
    jira_base = os.environ.get('JIRA_BASE')
    jira_login = os.environ.get('JIRA_LOGIN')
    jira_api_token = os.environ.get('JIRA_API_TOKEN')
    account_id = os.environ.get('ACCOUNT_ID')
    
    if not all([jira_base, jira_login, jira_api_token, account_id]):
        log("ERROR: Required environment variables not set")
        return False
    
    # Create Basic Auth header
    credentials = f"{jira_login}:{jira_api_token}"
    auth_string = base64.b64encode(credentials.encode()).decode()
    auth_header = f"Basic {auth_string}"
    
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }
    
    log("Fetching open AIS issue keys...")
    
    # Search for open issues
    search_url = f"{jira_base}/rest/api/3/search/jql"
    search_data = {
        "jql": 'project = AIS AND status = "Open"',
        "fields": ["key", "id"],
        "maxResults": 50
    }
    
    status, response_body = make_request(search_url, method='POST', data=search_data, headers=headers)
    
    if status != 200:
        log(f"Error fetching issues: HTTP {status}")
        log(f"Response: {response_body}")
        return False
    
    try:
        search_result = json.loads(response_body)
        issues = search_result.get('issues', [])
    except json.JSONDecodeError as e:
        log(f"Error parsing JSON: {e}")
        return False
    
    if not issues:
        log("No open issues found.")
        return True
    
    log(f"Found {len(issues)} open issues.")
    
    success_count = 0
    failure_count = 0
    
    for issue in issues:
        issue_key = issue.get('key')
        if not issue_key:
            continue
        
        log(f"Processing issue {issue_key}...")
        
        # Add comment
        comment_url = f"{jira_base}/rest/api/3/issue/{issue_key}/comment"
        comment_data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Hello 👋 — Automated comment from AWS Lambda."
                            }
                        ]
                    }
                ]
            }
        }
        
        status, _ = make_request(comment_url, method='POST', data=comment_data, headers=headers)
        log(f"Comment HTTP status: {status}")
        
        if status < 200 or status >= 300:
            log(f"✗ Failed to add comment to {issue_key}")
            failure_count += 1
            continue
        
        log(f"✓ Comment added to {issue_key}")
        
        # Assign issue
        assign_url = f"{jira_base}/rest/api/3/issue/{issue_key}/assignee"
        assign_data = {"accountId": account_id}
        
        status, _ = make_request(assign_url, method='PUT', data=assign_data, headers=headers)
        log(f"Assignment HTTP status: {status}")
        
        # Transition issue
        transition_url = f"{jira_base}/rest/api/3/issue/{issue_key}/transitions"
        transition_data = {"transition": {"id": "31"}}
        
        status, _ = make_request(transition_url, method='POST', data=transition_data, headers=headers)
        log(f"Transition HTTP status: {status}")
        
        if status >= 200 and status < 300:
            success_count += 1
        else:
            failure_count += 1
    
    log(f"Summary: Success={success_count}, Failures={failure_count}")
    return failure_count == 0

if __name__ == "__main__":
    success = run_automation()
    exit(0 if success else 1)
