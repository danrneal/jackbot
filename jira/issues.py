from jira import jira


def issue_event(data):
    issue = data['issue']
    if issue['fields']['project']['key'] != jira.PROJ_KEY:
        return
    jira.get_issue(issue['key'])
