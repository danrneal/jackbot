import os
import queue
import schedule
import time
from jira import jira
from slack import webhooks

ALERT_TIME = '09:00'
live = False
WEBHOOK_URL = os.environ.get('SLACK_LIVE_WEBHOOK_URL')
if WEBHOOK_URL:
    live = True
sched_q = queue.Queue()


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
        burndown_issues = []
        for issue in sprint_issues:
            if issue['fields']['status']['statusCategory']['name'] != 'Done':
                if issue['fields']['issuetype']['name'] != 'Story':
                    burndown_issues.append({
                        'key': issue['key'],
                        'type': 'bug'
                    })
        get_message_info(sprint_name, burndown_issues)


def get_message_info(sprint_name, burndown_issues):
    burndown = 0
    estimate_missing = []
    for issue in burndown_issues:
        estimate = jira.get_estimate(issue['key'])
        if estimate:
            burndown += estimate
        else:
            estimate_missing.append(issue)
    webhooks.build_message(
        {
            'name': sprint_name,
            'burndown': int(burndown)
        }, estimate_missing
    )


def scheduler():
    schedule.every().monday.at(ALERT_TIME).do(get_active_sprint_info)
    schedule.every().tuesday.at(ALERT_TIME).do(get_active_sprint_info)
    schedule.every().wednesday.at(ALERT_TIME).do(get_active_sprint_info)
    schedule.every().thursday.at(ALERT_TIME).do(get_active_sprint_info)
    schedule.every().friday.at(ALERT_TIME).do(get_active_sprint_info)
    while True:
        try:
            data = sched_q.get(block=False)
            if data == 'shutdown':
                break
        except queue.Empty:
            schedule.run_pending()
            time.sleep(1)
