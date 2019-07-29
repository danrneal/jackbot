import base64
import datetime
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


def get_active_sprint():
    url = f"/rest/agile/1.0/board/{BOARD_ID}/sprint"
    response = api_call("GET", url)
    sprints = json.loads(response)['values']
    active_sprint = next((
        sprint
        for sprint
        in sprints
        if sprint['state'] == 'active'),
        None
    )
    return active_sprint


def create_sprint(name, board_id):
    url = '/rest/agile/1.0/sprint'
    payload = {
        "name": name,
        "originBoardId": board_id
    }
    sprint = api_call("POST", url, data=payload)
    return json.loads(sprint)


def start_sprint(sprint_id):
    url = f"/rest/agile/1.0/sprint/{sprint_id}"
    start_date = datetime.datetime.now()
    end_date = start_date + datetime.timedelta(days=14)
    payload = {
        "state": "active",
        "startDate": start_date.astimezone().isoformat(),
        "endDate": end_date.astimezone().isoformat(),
    }
    api_call("POST", url, data=payload)


def delete_sprint(sprint_id):
    url = f"/rest/agile/1.0/sprint/{sprint_id}"
    api_call("DELETE", url)


def get_issues_for_sprint(sprint_id):
    url = f"/rest/agile/1.0/sprint/{sprint_id}/issue"
    response = api_call("GET", url)
    max_results = json.loads(response)['maxResults']
    start_at = json.loads(response)['startAt']
    total = json.loads(response)['total']
    sprint_issues = json.loads(response)['issues']
    while start_at + max_results < total:
        start_at += max_results
        url = f"/rest/agile/1.0/sprint/{sprint_id}/issue?startAt={start_at}"
        response = api_call("GET", url)
        sprint_issues += json.loads(response)['issues']
    return sprint_issues


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


def get_issue(issue_key):
    url = f"/rest/agile/1.0/issue/{issue_key}"
    issue = api_call("GET", url)
    return json.loads(issue)


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


def search_for_issue(issuetype, summary, parent_key=None):
    jql = f'project={PROJ_KEY}%26issuetype="{issuetype}"%26summary~"{summary}"'
    if parent_key:
        jql += f"%26parent={parent_key}"
    url = f"/rest/api/3/search?jql={jql}"
    response = api_call("GET", url)
    issues = json.loads(response)['issues']
    if len(issues) == 0:
        return None
    else:
        return issues[0]


def create_issue(issuetype, summary, parent_key=None, **kwargs):
    url = "/rest/api/3/issue"
    payload = {
        "fields": {**{
            "project": {
                "key": PROJ_KEY
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
    else:
        payload['fields']['description'] = {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{
                    "type": "text",
                    "text": "Test issue created by JackBot"
                }]
            }]
        }
    issue = api_call("POST", url, data=payload)
    return json.loads(issue)


def delete_issue(issue_key, delete_subtasks=False):
    url = f"/rest/api/3/issue/{issue_key}?deleteSubtasks={delete_subtasks}"
    api_call("DELETE", url)


def get_transition_id(issue_key, transition_name):
    url = f"/rest/api/3/issue/{issue_key}/transitions"
    response = api_call("GET", url)
    transitions = json.loads(response)['transitions']
    transition_id = next(
        transition['id']
        for transition
        in transitions
        if transition["name"].strip() == transition_name
    )
    return transition_id


def transition_issue(issue_key, transition_name, resolution=None):
    transition_id = get_transition_id(issue_key, transition_name)
    url = f"/rest/api/3/issue/{issue_key}/transitions"
    payload = {
        "transition": {
            "id": transition_id
        }
    }
    if resolution:
        payload['fields'] = {
            "resolution": {
                "name": resolution
            }
        }
    api_call("POST", url, data=payload)


def generate_file(data, filename=None):
    if not os.path.exists('functional_tests/datadumps'):
        os.makedirs('functional_tests/datadumps')
    i = 1
    while os.path.exists(f'functional_tests/datadumps/webhook-{i:02d}.json'):
        i += 1
    if not filename:
        filename = f'functional_tests/datadumps/webhook-{i:02d}.json'
    with open(filename, 'w') as outfile:
        outfile.write(json.dumps(data, indent=2))
