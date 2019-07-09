import unittest
from unittest.mock import patch
from slack.webhooks import (
    build_message, build_burndown_block, build_estimates_missing_block,
    build_large_estimates_block
)


class WebhooksTest(unittest.TestCase):

    @patch('slack.slack.send_message')
    @patch('slack.webhooks.build_burndown_block')
    @patch('slack.webhooks.build_estimates_missing_block')
    @patch('slack.webhooks.build_large_estimates_block')
    def test_build_message_ignores_empty_lists(
        self, mock_build_large_estimates_block,
        mock_build_missing_estimates_block, mock_build_burndown_block,
        mock_send_message
    ):
        build_message({
            'name': 'TEST Sprint',
            'burndown': 21
        }, [], [])
        mock_build_burndown_block.assert_called_once_with({
            'name': 'TEST Sprint',
            'burndown': 21
        })
        mock_build_missing_estimates_block.assert_not_called()
        mock_build_large_estimates_block.assert_not_called()
        mock_send_message.assert_called_once()

    @patch('slack.slack.send_message')
    @patch('slack.webhooks.build_burndown_block')
    @patch('slack.webhooks.build_estimates_missing_block')
    @patch('slack.webhooks.build_large_estimates_block')
    def test_build_message_builds_missing_estimate_block_when_appropriate(
        self, mock_build_large_estimates_block,
        mock_build_missing_estimates_block, mock_build_burndown_block,
        mock_send_message
    ):
        build_message(
            {
                'name': 'TEST Sprint',
                'burndown': 21
            },
            [{
                'key': 'TEST-1',
                'type': 'bug'
            }], []
        )
        mock_build_burndown_block.assert_called_once_with({
            'name': 'TEST Sprint',
            'burndown': 21
        })
        mock_build_missing_estimates_block.assert_called_once_with([{
                'key': 'TEST-1',
                'type': 'bug'
        }])
        mock_build_large_estimates_block.assert_not_called()
        mock_send_message.assert_called_once()

    @patch('slack.slack.send_message')
    @patch('slack.webhooks.build_burndown_block')
    @patch('slack.webhooks.build_estimates_missing_block')
    @patch('slack.webhooks.build_large_estimates_block')
    def test_build_message_builds_large_estimate_block_when_appropriate(
        self, mock_build_large_estimates_block,
        mock_build_missing_estimates_block, mock_build_burndown_block,
        mock_send_message
    ):
        build_message(
            {
                'name': 'TEST Sprint',
                'burndown': 21
            }, [],
            [{
                'key': 'TEST-1',
                'type': 'task'
            }]
        )
        mock_build_burndown_block.assert_called_once_with({
            'name': 'TEST Sprint',
            'burndown': 21
        })
        mock_build_large_estimates_block.assert_called_once_with([{
                'key': 'TEST-1',
                'type': 'task'
        }])
        mock_build_missing_estimates_block.assert_not_called()
        mock_send_message.assert_called_once()

    def test_burndown_block_is_built(self):
        burndown_block = build_burndown_block({
            'name': 'TEST Sprint',
            'burndown': 21
        })
        self.assertIn('TEST Sprint', str(burndown_block))
        self.assertIn('21', str(burndown_block))

    def test_estimates_missing_block_is_built(self):
        estimates_missing_block = build_estimates_missing_block([{
            'key': 'TEST-1',
            'type': 'bug'
        }])
        self.assertIn('TEST-1', str(estimates_missing_block))
        self.assertIn('jira_bug', str(estimates_missing_block))

    def test_large_estimates_block_is_built(self):
        large_estimates_block = build_large_estimates_block([{
            'key': 'TEST-1',
            'type': 'task'
        }])
        self.assertIn('TEST-1', str(large_estimates_block))
        self.assertIn('jira_task', str(large_estimates_block))