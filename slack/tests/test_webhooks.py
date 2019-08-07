import unittest
from unittest.mock import patch
from slack.webhooks import (
    build_message, build_burndown_block, build_issue_str,
    build_estimates_missing_block, build_large_estimates_block,
    build_no_subtasks_block
)


@patch('slack.slack.send_message')
@patch('slack.webhooks.build_large_estimates_block')
@patch('slack.webhooks.build_estimates_missing_block')
@patch('slack.webhooks.build_no_subtasks_block')
@patch('slack.webhooks.build_burndown_block')
class BuildMessageTest(unittest.TestCase):

    sprint_info = {
        'name': 'TEST Sprint',
        'burndown': 21
    }

    issues = [{
        'key': 'TEST-1',
        'assignee': 'someone'
    }]

    def test_build_message_ignores_empty_lists(
        self, mock_build_burndown_block, mock_build_no_subtasks_block,
        mock_build_estimates_missing_block, mock_build_large_estimates_block,
        mock_send_message
    ):
        build_message(self.sprint_info, [], [], [])
        mock_build_burndown_block.assert_called_once_with(self.sprint_info)
        mock_build_no_subtasks_block.assert_not_called()
        mock_build_estimates_missing_block.assert_not_called()
        mock_build_large_estimates_block.assert_not_called()
        mock_send_message.assert_called_once()

    def test_build_message_builds_no_subtasks_block_when_appropriate(
        self, mock_build_burndown_block, mock_build_no_subtasks_block,
        mock_build_estimates_missing_block, mock_build_large_estimates_block,
        mock_send_message
    ):
        self.issues[0]['type'] = 'story'
        build_message(self.sprint_info, self.issues, [], [])
        mock_build_burndown_block.assert_called_once_with(self.sprint_info)
        mock_build_no_subtasks_block.assert_called_once_with(self.issues)
        mock_build_estimates_missing_block.assert_not_called()
        mock_build_large_estimates_block.assert_not_called()
        mock_send_message.assert_called_once()

    def test_build_message_builds_estimates_missing_block_when_appropriate(
        self, mock_build_burndown_block, mock_build_no_subtasks_block,
        mock_build_estimates_missing_block, mock_build_large_estimates_block,
        mock_send_message
    ):
        self.issues[0]['type'] = 'bug'
        build_message(self.sprint_info, [], self.issues, [])
        mock_build_burndown_block.assert_called_once_with(self.sprint_info)
        mock_build_no_subtasks_block.assert_not_called()
        mock_build_estimates_missing_block.assert_called_once_with(self.issues)
        mock_build_large_estimates_block.assert_not_called()
        mock_send_message.assert_called_once()

    def test_build_message_builds_large_estimates_block_when_appropriate(
        self, mock_build_burndown_block, mock_build_no_subtasks_block,
        mock_build_estimates_missing_block, mock_build_large_estimates_block,
        mock_send_message
    ):
        self.issues[0]['type'] = 'task'
        build_message(self.sprint_info, [], [], self.issues)
        mock_build_burndown_block.assert_called_once_with(self.sprint_info)
        mock_build_no_subtasks_block.assert_not_called()
        mock_build_estimates_missing_block.assert_not_called()
        mock_build_large_estimates_block.assert_called_once_with(self.issues)
        mock_send_message.assert_called_once()


class BuildMessageBlocksTest(unittest.TestCase):

    issues = [{
        'key': 'TEST-1',
        'assignee': None
    }]

    def test_burndown_block_is_built(self):
        burndown_block = build_burndown_block({
            'name': 'TEST Sprint',
            'burndown': 21,
            'assignee': 'someone'
        })
        self.assertIn('TEST Sprint', str(burndown_block))
        self.assertIn('21', str(burndown_block))

    def test_unassigned_issues_assignee_is_ignored(self):
        self.issues[0]['type'] = 'story'
        self.issues[0]['assignee'] = None
        issue_str = build_issue_str('', self.issues)
        self.assertNotIn(str(self.issues[0]['assignee']), str(issue_str))

    def test_no_subtasks_block_is_built(self):
        self.issues[0]['type'] = 'story'
        self.issues[0]['assignee'] = 'someone'
        no_subtasks_block = build_no_subtasks_block(self.issues)
        self.assertIn('TEST-1', str(no_subtasks_block))
        self.assertIn('jira_story', str(no_subtasks_block))
        self.assertIn('someone', str(no_subtasks_block))

    def test_estimates_missing_block_is_built(self):
        self.issues[0]['type'] = 'bug'
        self.issues[0]['assignee'] = 'someone'
        estimates_missing_block = build_estimates_missing_block(self.issues)
        self.assertIn('TEST-1', str(estimates_missing_block))
        self.assertIn('jira_bug', str(estimates_missing_block))
        self.assertIn('someone', str(estimates_missing_block))

    def test_large_estimates_block_is_built(self):
        self.issues[0]['type'] = 'task'
        self.issues[0]['assignee'] = 'someone'
        large_estimates_block = build_large_estimates_block(self.issues)
        self.assertIn('TEST-1', str(large_estimates_block))
        self.assertIn('jira_task', str(large_estimates_block))
        self.assertIn('someone', str(large_estimates_block))
