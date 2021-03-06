from jira import jira
from slack import slack


def build_message(
    sprint_info, no_subtasks=None, estimates_missing=None, large_estimates=None
):
    message = build_burndown_block(sprint_info)
    if no_subtasks:
        message['blocks'].extend(
            build_no_subtasks_block(no_subtasks)
        )
    if estimates_missing:
        message['blocks'].extend(
            build_estimates_missing_block(estimates_missing)
        )
    if large_estimates:
        message['blocks'].extend(
            build_large_estimates_block(large_estimates)
        )
    slack.send_message(message)


def build_burndown_block(sprint_info):
    sprint_url = f"{jira.SERVER}/secure/RapidBoard.jspa"
    sprint_url += f"?rapidView={jira.BOARD_ID}"
    burndown_block = {
        "blocks": [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":fire::fire::fire:BURNDOWN ALERT:fire::fire::fire:"
            },
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Sprint:*\n<{sprint_url}|{sprint_info['name']}>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Hours Remaining:*\n{sprint_info['burndown']}"
                }
            ]
        }]
    }
    return burndown_block


def build_issue_str(field_header, issues):
    issue_str = field_header
    for issue in issues:
        url = f"{jira.SERVER}/browse/{issue['key']}"
        issue_str += f"\n<{url}|:jira_{issue['type']}: {issue['key']}>"
        if issue.get('assignee'):
            issue_str += f"    ({issue['assignee']})"
    return issue_str


def build_no_subtasks_block(no_subtasks):
    no_subtasks_block = (
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "These stories don't have any tasks, consider adding some"
                )
            },
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": build_issue_str("*Stories:*", no_subtasks)
                }
            ]
        }
    )
    return no_subtasks_block


def build_estimates_missing_block(estimates_missing):
    estimates_missing_block = (
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "These issues don't have an estimate, consider adding one"
                )
            },
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": build_issue_str("*Issues:*", estimates_missing)
                }
            ]
        }
    )
    return estimates_missing_block


def build_large_estimates_block(large_estimates):
    large_estimates_block = (
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "These tasks are pretty big, consider splitting them"
            },
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": build_issue_str("*Tasks:*", large_estimates)
                }
            ]
        }
    )
    return large_estimates_block
