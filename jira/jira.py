import base64
import json
import os
import requests

SERVER = 'https://moblab.atlassian.net'
EMAIL = 'dan.neal@moblab.com'
PROJ_KEY = "EDU"
BOARD_ID = 17

api_token = base64.b64encode(
    bytes(f"{EMAIL}:{os.environ['JIRA_API_TOKEN']}", 'utf-8')
).decode('utf-8')
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Basic {api_token}"
}


def api_call(method, endpoint, data=None):
    url = f"{SERVER}{endpoint}"
    if data:
        data = json.dumps(data)
    response = requests.request(method, url, data=data, headers=headers)
    if not response.ok:
        print(response.text)
        response.raise_for_status()
    return response.text


def create_sprint(name, board_id):
    url = '/rest/agile/1.0/sprint'
    payload = {
        "name": name,
        "originBoardId": board_id
    }
    sprint = api_call("POST", url, data=payload)
    return json.loads(sprint)


def get_issues_for_sprint(sprint_id):
    url = f"/rest/agile/1.0/sprint/{sprint_id}/issue"
    sprint_issues = api_call("GET", url)
    return json.loads(sprint_issues)['issues']


def add_issues_to_sprint(sprint_id, issue_keys):
    url = f"/rest/agile/1.0/sprint/{sprint_id}/issue"
    payload = {
        "issues": issue_keys
    }
    api_call("POST", url, data=payload)


def remove_issues_from_sprint(issue_keys):
    url = "/rest/agile/1.0/backlog/issue"
    payload = {
        'issues': issue_keys
    }
    api_call("POST", url, data=payload)


def delete_sprint(sprint_id):
    url = f"/rest/agile/1.0/sprint/{sprint_id}"
    api_call("DELETE", url)


def get_issue(issue_key):
    url = f"/rest/agile/1.0/issue/{issue_key}"
    issue = api_call("GET", url)
    return json.loads(issue)


def create_issue(project_key, issuetype, summary, parent_key=None, **kwargs):
    url = "/rest/api/3/issue"
    payload = {
        "fields": {**{
            "project": {
                "key": project_key
            },
            "issuetype": {
                "name": issuetype
            },
            "summary": summary
        }, **kwargs}
    }
    if parent_key:
        payload['fields']['parent'] = {
            "key": parent_key
        }
    issue = api_call("POST", url, data=payload)
    return json.loads(issue)


def delete_issue(issue_key, delete_subtasks=False):
    url = f"/rest/api/3/issue/{issue_key}?deleteSubtasks={delete_subtasks}"
    api_call("DELETE", url)


def get_estimate(issue_key):
    url = f"/rest/agile/1.0/issue/{issue_key}/estimation?boardId={BOARD_ID}"
    estimate = api_call("GET", url)
    return json.loads(estimate).get('value')


def get_estimate_field(issue_key):
    url = f"/rest/agile/1.0/issue/{issue_key}/estimation?boardId={BOARD_ID}"
    estimate = api_call("GET", url)
    return json.loads(estimate).get('fieldId')


def update_estimate(issue_key, estimate):
    url = f"/rest/agile/1.0/issue/{issue_key}/estimation?boardId={BOARD_ID}"
    payload = {
        'value': estimate
    }
    api_call("PUT", url, data=payload)
