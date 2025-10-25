import json
import os
import base64
import urllib.request
import urllib.error
from datetime import datetime

def lambda_handler(event, context):
    try:
        # Get credentials from environment
        jira_base = os.environ['JIRA_BASE']
        jira_login = os.environ['JIRA_LOGIN']
        jira_token = os.environ['JIRA_API_TOKEN']
        account_id = os.environ['ACCOUNT_ID']
        
        # Create auth header
        auth_string = f"{jira_login}:{jira_token}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json'
        }
        
        print(f"[{datetime.now()}] Searching for open issues...")
        
        # Search
        jql_data = json.dumps({
            "jql": 'project=AIS AND status IN (Open, "Work in progress")',
            "fields": ["key"],
            "maxResults": 50
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{jira_base}/rest/api/3/search/jql",
            data=jql_data,
            headers=headers,
            method='POST'
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"HTTP Error {e.code}: {error_body}")
            raise
        
        issues = [issue['key'] for issue in result.get('issues', [])]
        
        if not issues:
            print(f"[{datetime.now()}] No open issues found")
            return {'statusCode': 200, 'body': 'No issues to process'}
        
        print(f"[{datetime.now()}] Found issues: {', '.join(issues)}")
        
        # Process each issue
        processed = 0
        for issue_key in issues:
            print(f"[{datetime.now()}] Processing {issue_key}...")
            
            try:
                # Add comment
                comment_data = json.dumps({
                    "body": {
                        "type": "doc",
                        "version": 1,
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "✓ Automated comment from Lambda"}]
                        }]
                    }
                }).encode('utf-8')
                
                req = urllib.request.Request(
                    f"{jira_base}/rest/api/3/issue/{issue_key}/comment",
                    data=comment_data,
                    headers=headers,
                    method='POST'
                )
                urllib.request.urlopen(req)
                print(f"[{datetime.now()}] Added comment to {issue_key}")
                
                # Assign issue
                assign_data = json.dumps({"accountId": account_id}).encode('utf-8')
                req = urllib.request.Request(
                    f"{jira_base}/rest/api/3/issue/{issue_key}/assignee",
                    data=assign_data,
                    headers=headers,
                    method='PUT'
                )
                urllib.request.urlopen(req)
                print(f"[{datetime.now()}] Assigned {issue_key}")
                
                # Transition (with error handling)
                try:
                    transition_data = json.dumps({"transition": {"id": "31"}}).encode('utf-8')
                    req = urllib.request.Request(
                        f"{jira_base}/rest/api/3/issue/{issue_key}/transitions",
                        data=transition_data,
                        headers=headers,
                        method='POST'
                    )
                    urllib.request.urlopen(req)
                    print(f"[{datetime.now()}] Transitioned {issue_key}")
                except urllib.error.HTTPError as e:
                    if e.code == 400:
                        print(f"[{datetime.now()}] Skipping transition for {issue_key} (already in target state or invalid transition)")
                    else:
                        raise
                
                processed += 1
                
            except Exception as e:
                print(f"[{datetime.now()}] Error processing {issue_key}: {str(e)}")
                # Continue to next issue
                continue
        
        print(f"[{datetime.now()}] Done! Processed {processed}/{len(issues)} issues")
        return {'statusCode': 200, 'body': f'Processed {processed}/{len(issues)} issues'}
    
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}
