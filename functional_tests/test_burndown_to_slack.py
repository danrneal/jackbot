import os
from functional_tests.base import FunctionalTest
from jira import jira
from slack import slack

WEBHOOK_URL = os.environ['SLACK_TEST_WEBHOOK_URL']
CHANNEL_ID = os.environ['SLACK_TEST_CHANNEL_ID']


class BurndownTest(FunctionalTest):

    def test_burndown_delevered_to_slack(self):
        # Abe add some issues to a sprint with estimates. He then starts the
        # sprint. There is a notification in Slack with correct burndown number.
        parent = jira.get_issue(self.issue_keys[0])
        subtasks = parent['fields']['subtasks']
        jira.update_estimate(subtasks[0]['key'], 8)
        jira.update_estimate(subtasks[1]['key'], 3)
        parent = jira.get_issue(self.issue_keys[2])
        subtasks = parent['fields']['subtasks']
        jira.update_estimate(subtasks[0]['key'], 5)
        jira.update_estimate(subtasks[1]['key'], 2)
        jira.add_issues_to_sprint(self.sprint_id, self.issue_keys[:2])
        jira.start_sprint(self.sprint_id)
        message = slack.get_message(CHANNEL_ID, WEBHOOK_URL)
        self.assertIn('Burndown', message['text'])
        self.assertIn('18 hours', message['text'])
