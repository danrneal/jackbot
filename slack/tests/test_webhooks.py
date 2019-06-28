import unittest
from unittest.mock import patch
from slack.webhooks import build_message


class WebhooksTest(unittest.TestCase):

    @patch('slack.slack.send_message')
    def test_webhook_passes_well_formed_message(self, mock_send_message):
        build_message(21, 'TEST Sprint')
        mock_send_message.assert_called_once()
