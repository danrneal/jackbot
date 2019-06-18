import json
import os
import requests
from jira import jira


def issue_event(data):
    issue = data['issue']
    if not valid_issue(issue):
        return
    get_parent_issue(issue)


def valid_issue(issue):
    issuetype = issue['fields']['issuetype']
    proj_key = issue['fields']['project']['key']
    if (
        proj_key == jira.PROJ_KEY and
        (issuetype['name'] == 'Story' or issuetype['subtask'])
    ):
        return True
    else:
        return False


def get_parent_issue(issue):
    try:
        if issue['fields']['issuetype']['subtask']:
            parent_issue = jira.get_issue(issue['fields']['parent']['key'])
        else:
            parent_issue = jira.get_issue(issue['key'])
        get_issues_to_estimate(parent_issue)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 404:
            raise


def get_issues_to_estimate(issue):
    sprint = issue['fields']['sprint']
    if not sprint:
        set_backlog_issue_estimate(issue['key'])
    else:
        sprint_issues = jira.get_issues_for_sprint(sprint['id'])
        set_issue_estimates(sprint_issues)


def set_backlog_issue_estimate(issue_key):
    estimate = jira.get_estimate(issue_key)
    if estimate:
        jira.update_estimate(issue_key, None)


def set_issue_estimates(issues):
    for issue in issues:
        estimate = 0
        for subtask in issue['fields']['subtasks']:
            subtask_estimate = jira.get_estimate(subtask['key'])
            if subtask_estimate:
                estimate += subtask_estimate
        if estimate != jira.get_estimate(issue['key']):
            jira.update_estimate(issue['key'], estimate)


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
