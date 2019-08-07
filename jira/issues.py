import queue
import requests
from jira import jira

q = queue.Queue()


def issue_event(data):
    issue = data.get('issue')
    if issue and issue['fields']['project']['key'] == jira.PROJ_KEY:
        get_issue_sprint(issue['key'])


def get_issue_sprint(issue_key):
    try:
        issue = jira.get_issue(issue_key)
        sprint = issue['fields']['sprint']
        if sprint:
            round_sprint_issue_estimates(sprint['id'])
        else:
            get_backlog_parent_issue(issue)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 404:
            raise


def round_sprint_issue_estimates(sprint_id):
    sprint_issues = jira.get_issues_for_sprint(sprint_id)
    for issue in sprint_issues:
        estimate = jira.get_estimate(issue['key'])
        if estimate and not float(estimate).is_integer():
            jira.update_estimate(issue['key'], int(estimate) + 1)
    get_sprint_stories(sprint_issues)


def get_sprint_stories(sprint_issues):
    sprint_stories = [
        issue for issue in sprint_issues
        if issue['fields']['issuetype']['name'] == 'Story'
    ]
    for story in sprint_stories:
        story['fields']['subtasks'] = [
            subtask for subtask in story['fields']['subtasks']
            if subtask['fields']['status']['name'] != 'Archive'
        ]
        set_story_status(story)
        set_story_estimate(story)


def set_story_status(story):
    current_story_status = story['fields']['status']['name']
    unique_subtask_statuses = list(set([
        subtask['fields']['status']['name']
        for subtask in story['fields']['subtasks']
    ]))
    if unique_subtask_statuses in ([], ['Backlog']):
        new_story_status = 'Backlog'
    elif unique_subtask_statuses == ['Done']:
        if current_story_status == 'Done':
            new_story_status = 'Done'
        else:
            new_story_status = 'PO Review'
    else:
        new_story_status = 'In Progress'
    if current_story_status != new_story_status:
        jira.transition_issue(story['key'], new_story_status)


def set_story_estimate(story):
    current_story_estimate = jira.get_estimate(story['key'])
    new_story_estimate = 0
    for subtask in story['fields']['subtasks']:
        subtask_estimate = jira.get_estimate(subtask['key'])
        if subtask_estimate:
            new_story_estimate += subtask_estimate
    if current_story_estimate != new_story_estimate:
        jira.update_estimate(story['key'], new_story_estimate)


def get_backlog_parent_issue(issue):
    if issue['fields'].get('parent'):
        parent_key = issue['fields']['parent']['key']
        issue = jira.get_issue(parent_key)
    set_backlog_parent_issue_status(issue)
    set_backlog_parent_issue_assignee(issue)
    set_backlog_parent_issue_estimate(issue['key'])


def set_backlog_parent_issue_status(issue):
    issue_status = issue['fields']['status']['name']
    if issue_status != "Backlog":
        jira.transition_issue(issue['key'], "Backlog")


def set_backlog_parent_issue_assignee(issue):
    if issue['fields']['assignee']:
        jira.assign_issue(issue['key'], None)


def set_backlog_parent_issue_estimate(issue_key):
    estimate = jira.get_estimate(issue_key)
    if estimate is not None:
        jira.update_estimate(issue_key, None)
