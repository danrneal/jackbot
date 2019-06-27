from jira import jira
from slack import webhooks


def sprint_started(data):
    sprint = data.get('sprint')
    if sprint['originBoardId'] == jira.BOARD_ID:
        get_burndown_issues(sprint['id'], sprint['name'])


def get_active_sprint_info():
    sprint = jira.get_active_sprint()
    get_burndown_issues(sprint['id'], sprint['name'])


def get_burndown_issues(sprint_id, sprint_name):
    sprint_issues = jira.get_issues_for_sprint(sprint_id)
    burndown_issue_keys = [
        issue['key'] for issue in sprint_issues
        if (
            issue['fields']['issuetype']['name'] != 'Story' and
            issue['fields']['status']['statusCategory']['name'] != 'Done'
        )
    ]
    add_issue_estimates(burndown_issue_keys, sprint_name)


def add_issue_estimates(issue_keys, sprint_name):
    burndown = 0
    for issue_key in issue_keys:
        estimate = jira.get_estimate(issue_key)
        if estimate:
            burndown += estimate
    webhooks.build_message(burndown, sprint_name)