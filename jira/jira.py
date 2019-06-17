from base64 import b64encode
import json
import os
import requests

SERVER = 'https://moblab.atlassian.net'
EMAIL = 'dan.neal@moblab.com'
PROJ_KEY = "EDU"
BOARD_ID = 17

api_token = b64encode(
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