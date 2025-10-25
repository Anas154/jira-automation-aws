#!/bin/bash
set -euo pipefail

# Error handling
trap 'echo "Error on line $LINENO"; exit 1' ERR

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

# Validate environment variables
if [ -z "${JIRA_BASE:-}" ] || [ -z "${JIRA_LOGIN:-}" ] || [ -z "${JIRA_API_TOKEN:-}" ] || [ -z "${ACCOUNT_ID:-}" ]; then
    log "ERROR: Required environment variables are not set"
    log "Required: JIRA_BASE, JIRA_LOGIN, JIRA_API_TOKEN, ACCOUNT_ID"
    exit 1
fi

# Prepare Basic Auth header
AUTH_HEADER="Authorization: Basic $(echo -n "${JIRA_LOGIN}:${JIRA_API_TOKEN}" | base64 | tr -d '\n')"

log "Fetching open AIS issue keys..."

# Fetch all open AIS issue keys
issue_keys=$(curl -s -X POST "${JIRA_BASE}/rest/api/3/search/jql" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  --data '{"jql":"project = AIS AND status = \"Open\"","fields":["key","id"],"maxResults":50}' \
  | jq -r '.issues[] | (.key // .id) | select(. != null and . != "null")')

if [ -z "$issue_keys" ]; then
  log "No open issues found."
  exit 0
fi

mapfile -t issues <<< "$issue_keys"
log "Found ${#issues[@]} open issues."

SUCCESS_COUNT=0
FAILURE_COUNT=0

for issue in "${issues[@]}"
do
  log "Processing $issue..."

  # Add comment to issue
  response=$(curl -s -X POST "${JIRA_BASE}/rest/api/3/issue/${issue}/comment" \
    -H "$AUTH_HEADER" -H "Content-Type: application/json" \
    --data '{
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
    }' -w "\n%{http_code}")

  body=$(printf "%s" "$response" | sed '$d')
  code=$(printf "%s" "$response" | tail -n1)
  log "Comment HTTP status: $code"

  if [ "$code" -ge 200 ] && [ "$code" -lt 300 ]; then
    log "✓ Comment added to $issue"
  else
    log "✗ Failed to add comment to $issue"
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    continue
  fi

  # Assign issue
  assign_response=$(curl -s -X PUT "${JIRA_BASE}/rest/api/3/issue/${issue}/assignee" \
    -H "$AUTH_HEADER" -H "Content-Type: application/json" \
    --data "{\"accountId\":\"${ACCOUNT_ID}\"}" -w "\n%{http_code}")

  assign_code=$(echo "$assign_response" | tail -n1)
  log "Assignment HTTP status: $assign_code"

  # Transition issue
  transition_response=$(curl -s -X POST "${JIRA_BASE}/rest/api/3/issue/${issue}/transitions" \
    -H "$AUTH_HEADER" -H "Content-Type: application/json" \
    --data '{"transition":{"id":"31"}}' -w "\n%{http_code}")

  transition_code=$(echo "$transition_response" | tail -n1)
  log "Transition HTTP status: $transition_code"

  if [ "$transition_code" -ge 200 ] && [ "$transition_code" -lt 300 ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  else
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
  fi

done

log "Summary: Success=$SUCCESS_COUNT, Failures=$FAILURE_COUNT"
exit 0
