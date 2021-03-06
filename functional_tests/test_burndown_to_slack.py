import json
import os
from functional_tests.base import FunctionalTest
from jira import jira
from slack import slack

WEBHOOK_URL = os.environ['SLACK_TEST_WEBHOOK_URL']
CHANNEL_ID = os.environ['SLACK_TEST_CHANNEL_ID']


class BurndownTest(FunctionalTest):

    def test_burndown_delivered_to_slack(self):
        slack.clear_old_bot_messages(CHANNEL_ID, WEBHOOK_URL)

        # Abe adds some issues to a sprint with estimates. He then starts the
        # sprint. There is a notification in Slack with correct burndown number.
        parent = jira.get_issue(self.issue_keys[0])
        subtasks = parent['fields']['subtasks']
        jira.update_estimate(subtasks[0]['key'], 8)
        jira.transition_issue(subtasks[0]['key'], "Archive", "Won't Do")
        jira.update_estimate(subtasks[1]['key'], 20)
        parent = jira.get_issue(self.issue_keys[1])
        subtasks = parent['fields']['subtasks']
        jira.update_estimate(subtasks[0]['key'], 5)
        jira.update_estimate(subtasks[1]['key'], 2)
        jira.add_issues_to_sprint(self.sprint_id, self.issue_keys[:2])
        jira.start_sprint(self.sprint_id)
        message = slack.get_latest_bot_message(CHANNEL_ID, WEBHOOK_URL)
        self.assertIn('BURNDOWN', json.dumps(message))
        self.assertIn('27', json.dumps(message))

    def test_story_missing_estimate_to_slack(self):
        slack.clear_old_bot_messages(CHANNEL_ID, WEBHOOK_URL)

        # Abe adds a story without a subtask to the sprint. He then starts
        # the sprint. There is a notification in Slack detailing as much.
        jira.add_issues_to_sprint(self.sprint_id, [self.issue_keys[3]])
        jira.start_sprint(self.sprint_id)
        message = slack.get_latest_bot_message(CHANNEL_ID, WEBHOOK_URL)
        self.assertIn(self.issue_keys[3], json.dumps(message))

    def test_estimate_is_missing_to_slack(self):
        slack.clear_old_bot_messages(CHANNEL_ID, WEBHOOK_URL)

        # Abe adds a bug to the sprint without an estimate. He then
        # starts the sprint. There is a notification in Slack detailing as much.
        jira.add_issues_to_sprint(self.sprint_id, [self.issue_keys[4]])
        jira.start_sprint(self.sprint_id)
        message = slack.get_latest_bot_message(CHANNEL_ID, WEBHOOK_URL)
        self.assertIn(self.issue_keys[4], json.dumps(message))

    def test_estimate_is_too_big_to_slack(self):
        slack.clear_old_bot_messages(CHANNEL_ID, WEBHOOK_URL)

        # Abe adds a story task with a big estimate to the sprint. He then
        # starts the sprint. There is a notification in Slack detailing as much.
        parent = jira.get_issue(self.issue_keys[0])
        subtasks = parent['fields']['subtasks']
        jira.update_estimate(subtasks[0]['key'], 17)
        jira.update_estimate(subtasks[1]['key'], 5)
        jira.add_issues_to_sprint(self.sprint_id, [self.issue_keys[0]])
        jira.start_sprint(self.sprint_id)
        message = slack.get_latest_bot_message(CHANNEL_ID, WEBHOOK_URL)
        self.assertIn(subtasks[0]['key'], json.dumps(message))
        self.assertNotIn(subtasks[1]['key'], json.dumps(message))
