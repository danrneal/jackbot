import unittest
from unittest.mock import patch
from slack.webhooks import (
    build_message, build_burndown_block, build_issue_str,
    build_estimates_missing_block, build_large_estimates_block,
    build_no_subtasks_block
)


class WebhooksTest(unittest.TestCase):

    @patch('slack.slack.send_message')
    @patch('slack.webhooks.build_burndown_block')
    @patch('slack.webhooks.build_no_subtasks_block')
    @patch('slack.webhooks.build_estimates_missing_block')
    @patch('slack.webhooks.build_large_estimates_block')
    def test_build_message_ignores_empty_lists(
        self, mock_build_large_estimates_block,
        mock_build_missing_estimates_block, mock_build_no_subtasks_block,
        mock_build_burndown_block, mock_send_message
    ):
        sprint_info = {
            'name': 'TEST Sprint',
            'burndown': 21
        }
        build_message(sprint_info, [], [], [])
        mock_build_burndown_block.assert_called_once_with(sprint_info)
        mock_build_no_subtasks_block.assert_not_called()
        mock_build_missing_estimates_block.assert_not_called()
        mock_build_large_estimates_block.assert_not_called()
        mock_send_message.assert_called_once()

    @patch('slack.slack.send_message')
    @patch('slack.webhooks.build_burndown_block')
    @patch('slack.webhooks.build_no_subtasks_block')
    @patch('slack.webhooks.build_estimates_missing_block')
    @patch('slack.webhooks.build_large_estimates_block')
    def test_build_message_builds_no_subtasks_block_when_appropriate(
        self, mock_build_large_estimates_block,
        mock_build_missing_estimates_block, mock_build_no_subtasks_block,
        mock_build_burndown_block, mock_send_message
    ):
        sprint_info = {
            'name': 'TEST Sprint',
            'burndown': 21
        }
        no_subtasks = [{
            'key': 'TEST-1',
            'type': 'story',
            'assignee': 'test user'
        }]
        build_message(sprint_info, no_subtasks, [], [])
        mock_build_burndown_block.assert_called_once_with(sprint_info)
        mock_build_no_subtasks_block.assert_called_once_with(no_subtasks)
        mock_build_missing_estimates_block.assert_not_called()
        mock_build_large_estimates_block.assert_not_called()
        mock_send_message.assert_called_once()

    @patch('slack.slack.send_message')
    @patch('slack.webhooks.build_burndown_block')
    @patch('slack.webhooks.build_no_subtasks_block')
    @patch('slack.webhooks.build_estimates_missing_block')
    @patch('slack.webhooks.build_large_estimates_block')
    def test_build_message_builds_estimates_missing_block_when_appropriate(
        self, mock_build_large_estimates_block,
        mock_build_missing_estimates_block, mock_build_no_subtasks_block,
        mock_build_burndown_block, mock_send_message
    ):
        sprint_info = {
            'name': 'TEST Sprint',
            'burndown': 21
        }
        estimates_missing = [{
            'key': 'TEST-1',
            'type': 'bug',
            'assignee': 'test user'
        }]
        build_message(sprint_info, [], estimates_missing, [])
        mock_build_burndown_block.assert_called_once_with(sprint_info)
        mock_build_no_subtasks_block.assert_not_called()
        mock_build_missing_estimates_block.assert_called_once_with(
            estimates_missing)
        mock_build_large_estimates_block.assert_not_called()
        mock_send_message.assert_called_once()

    @patch('slack.slack.send_message')
    @patch('slack.webhooks.build_burndown_block')
    @patch('slack.webhooks.build_no_subtasks_block')
    @patch('slack.webhooks.build_estimates_missing_block')
    @patch('slack.webhooks.build_large_estimates_block')
    def test_build_message_builds_large_estimates_block_when_appropriate(
        self, mock_build_large_estimates_block,
        mock_build_missing_estimates_block, mock_build_no_subtasks_block,
        mock_build_burndown_block, mock_send_message
    ):
        sprint_info = {
            'name': 'TEST Sprint',
            'burndown': 21
        }
        large_estimates = [{
            'key': 'TEST-1',
            'type': 'task',
            'assignee': 'test user'
        }]
        build_message(sprint_info, [], [], large_estimates)
        mock_build_burndown_block.assert_called_once_with(sprint_info)
        mock_build_no_subtasks_block.assert_not_called()
        mock_build_missing_estimates_block.assert_not_called()
        mock_build_large_estimates_block.assert_called_once_with(
            large_estimates)
        mock_send_message.assert_called_once()

    def test_unassigned_issues_assignee_is_ignored(self):
        issues = [{
            'key': 'TEST-1',
            'type': 'story',
            'assignee': None
        }]
        issue_str = build_issue_str('', issues)
        self.assertNotIn(str(issues[0]['assignee']), str(issue_str))

    def test_burndown_block_is_built(self):
        burndown_block = build_burndown_block({
            'name': 'TEST Sprint',
            'burndown': 21,
            'assignee': 'test user'
        })
        self.assertIn('TEST Sprint', str(burndown_block))
        self.assertIn('21', str(burndown_block))

    def test_no_subtasks_block_is_built(self):
        no_subtasks_block = build_no_subtasks_block([{
            'key': 'TEST-1',
            'type': 'story',
            'assignee': 'test user'
        }])
        self.assertIn('TEST-1', str(no_subtasks_block))
        self.assertIn('jira_story', str(no_subtasks_block))
        self.assertIn('test user', str(no_subtasks_block))

    def test_estimates_missing_block_is_built(self):
        estimates_missing_block = build_estimates_missing_block([{
            'key': 'TEST-1',
            'type': 'bug',
            'assignee': 'test user'
        }])
        self.assertIn('TEST-1', str(estimates_missing_block))
        self.assertIn('jira_bug', str(estimates_missing_block))
        self.assertIn('test user', str(estimates_missing_block))

    def test_large_estimates_block_is_built(self):
        large_estimates_block = build_large_estimates_block([{
            'key': 'TEST-1',
            'type': 'task',
            'assignee': 'test user'
        }])
        self.assertIn('TEST-1', str(large_estimates_block))
        self.assertIn('jira_task', str(large_estimates_block))
        self.assertIn('test user', str(large_estimates_block))
