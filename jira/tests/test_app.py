import json
import unittest
from unittest.mock import patch
from jira.app import app, handle_webhook_from_q

app = app.test_client()


@patch('jira.app.q.put')
class WebhookTest(unittest.TestCase):

    def test_home_page_returns_correct_html(self, mock_q_put):
        response = app.get('/')
        mock_q_put.assert_not_called()
        self.assertEqual('JackBot is running!', response.data.decode())

    def test_post_request_data_gets_put_in_q(self, mock_q_put):
        response = app.post('/', data=json.dumps({"key": "value"}))
        mock_q_put.assert_called_once_with({"key": "value"})
        self.assertEqual(200, response.status_code)


class HandleWebhookFromQTest(unittest.TestCase):

    @patch('jira.app.q.get')
    def mock_handle_webhook_from_q(self, webhook, mock_q_get):
        mock_q_get.side_effect = [webhook, 'shutdown']
        handle_webhook_from_q()

    @patch('jira.app.sprint_event')
    @patch('jira.app.issue_event')
    def test_issue_event_passed_to_issue_event_func(
        self, mock_issue_event, mock_sprint_event
    ):
        webhook = {"issue": "Not None"}
        self.mock_handle_webhook_from_q(webhook)
        mock_issue_event.assert_called_once_with("Not None")
        mock_sprint_event.assert_not_called()

    @patch('jira.app.sprint_event')
    @patch('jira.app.issue_event')
    def test_sprint_started_event_passed_to_sprint_started_func(
        self, mock_issue_event, mock_sprint_event
    ):
        webhook = {"sprint": "Not None"}
        self.mock_handle_webhook_from_q(webhook)
        mock_issue_event.assert_not_called()
        mock_sprint_event.assert_called_once_with("Not None")

    @patch('jira.app.sprint_event')
    @patch('jira.app.issue_event')
    def test_other_events_get_discarded(
        self, mock_issue_event, mock_sprint_event
    ):
        webhook = {"anything_else": "something"}
        self.mock_handle_webhook_from_q(webhook)
        mock_issue_event.assert_not_called()
        mock_sprint_event.assert_not_called()
