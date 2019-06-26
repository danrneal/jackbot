import queue
import requests
from jira import jira

q = queue.Queue()


def issue_event(data):
    issue = data.get('issue')
    if issue and issue['fields']['project']['key'] != jira.PROJ_KEY:
        return
    get_issue_sprint(issue['key'])


def sprint_started(data):
    pass


def get_issue_sprint(issue_key):
    try:
        issue = jira.get_issue(issue_key)
        sprint = issue['fields']['sprint']
        if sprint:
            get_sprint_stories(sprint['id'])
        else:
            set_backlog_issue_estimate(issue)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 404:
            raise


def get_sprint_stories(sprint_id):
    sprint_issues = jira.get_issues_for_sprint(sprint_id)
    sprint_stories = [
        issue for issue in sprint_issues
        if issue['fields']['issuetype']['name'] == 'Story'
    ]
    set_issue_estimates(sprint_stories)


def set_backlog_issue_estimate(issue):
    if issue['fields'].get('parent'):
        issue_key = issue['fields']['parent']['key']
    else:
        issue_key = issue['key']
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
