import os
import schedule
import time
from jira import jira
from slack import webhooks

ALERT_TIME = '09:00'
live = False
WEBHOOK_URL = os.environ.get('SLACK_LIVE_WEBHOOK_URL')
if WEBHOOK_URL:
    live = True


def sprint_started(data):
    sprint = data.get('sprint')
    if sprint['originBoardId'] == jira.BOARD_ID:
        get_sprint_issues_by_type(sprint['id'], sprint['name'])


def get_active_sprint_info():
    sprint = jira.get_active_sprint()
    get_sprint_issues_by_type(sprint['id'], sprint['name'])


def get_sprint_issues_by_type(sprint_id, sprint_name):
    if (
        (sprint_name == 'TEST Sprint' and not live) or
        (sprint_name != 'TEST Sprint' and live)
    ):
        sprint_issues = jira.get_issues_for_sprint(sprint_id)
        bugs = []
        tasks = []
        stories_no_subtasks = []
        for issue in sprint_issues:
            if issue['fields']['status']['statusCategory']['name'] != 'Done':
                issuetype = issue['fields']['issuetype']['name']
                if issuetype in ['Bug', 'Critical']:
                    bugs.append({
                        'key': issue['key'],
                        'type': 'bug'
                    })
                elif issuetype in ['Task', 'Story Task']:
                    tasks.append({
                        'key': issue['key'],
                        'type': 'task'
                    })
                elif issuetype == 'Story' and not issue['fields']['subtasks']:
                    stories_no_subtasks.append({
                        'key': issue['key'],
                        'type': 'story'
                    })
        get_message_info(sprint_name, stories_no_subtasks, bugs, tasks)


def get_message_info(sprint_name, stories, bugs, tasks):
    burndown = 0
    no_subtasks = stories
    estimate_missing = []
    large_estimates = []
    for issue in bugs + tasks:
        estimate = jira.get_estimate(issue['key'])
        if estimate:
            burndown += estimate
            if issue['type'] == 'task' and estimate > 16:
                large_estimates.append(issue)
        else:
            estimate_missing.append(issue)
    sprint_info = {
        'name': sprint_name,
        'burndown': int(burndown)
    }
    webhooks.build_message(
        sprint_info, no_subtasks, estimate_missing, large_estimates
    )


def scheduler():
    schedule.every().monday.at(ALERT_TIME).do(get_active_sprint_info)
    schedule.every().tuesday.at(ALERT_TIME).do(get_active_sprint_info)
    schedule.every().wednesday.at(ALERT_TIME).do(get_active_sprint_info)
    schedule.every().thursday.at(ALERT_TIME).do(get_active_sprint_info)
    schedule.every().friday.at(ALERT_TIME).do(get_active_sprint_info)
    while True:
        schedule.run_pending()
        time.sleep(1)
