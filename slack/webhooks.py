from jira import jira
from slack import slack


def build_message(burndown, sprint_name):
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
                    "text": f"*Sprint:*\n<{sprint_url}|{sprint_name}>"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Hours Remaining:*\n{int(burndown)}"
                }
            ]
        }]
    }
    slack.send_message(message)
