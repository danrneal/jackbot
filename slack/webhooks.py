from jira import jira
from slack import slack


def build_message(sprint_info, estimates_missing=None):
    print('building')
    print(estimates_missing)
    message = build_burndown_block(sprint_info)
    if estimates_missing:
        message['blocks'].extend(
            build_estimates_missing_block(estimates_missing)
        )
        print('built')
    slack.send_message(message)


def build_burndown_block(sprint_info):
    sprint_url = f"{jira.SERVER}/secure/RapidBoard.jspa"
    sprint_url += f"?rapidView={jira.BOARD_ID}"
    message = {
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
    return message


def build_estimates_missing_block(estimates_missing):
    issue_str = "*Issues*:"
    for issue in estimates_missing:
        url = f"{jira.SERVER}/browse/{issue['key']}"
        issue_str += f"\n<{url}|:jira_{issue['type']}: {issue['key']}>"
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
                    "text": issue_str
                }
            ]
        }
    )
    return estimates_missing_block
