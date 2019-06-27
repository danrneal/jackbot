import unittest
from unittest.mock import Mock, patch
from slack import slack


class SlackTest(unittest.TestCase):

    @patch('requests.request')
    def test_send_message(self, mock_request):
        mock_request.return_value = Mock()
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = 'ok'
        slack.send_message('test message')
        mock_request.assert_called_once_with(
            "POST", slack.WEBHOOK_URL,
            data='test message',
            headers=slack.headers
        )
