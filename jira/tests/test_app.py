import json
import unittest
from unittest.mock import patch
from jira.app import app, handle_webhook_from_q

app = app.test_client()


class WebhookTest(unittest.TestCase):

    def test_home_page_returns_correct_html(self):
        response = app.get('/')
        self.assertEqual('JackBot is running!', response.data.decode())

    @patch('jira.app.q.put')
    def test_post_request_data_gets_put_in_q(self, mock_q_put):
        response = app.post('/', data=json.dumps({"key": "value"}))
        mock_q_put.assert_called_once_with({"key": "value"})
        self.assertEqual(200, response.status_code)

    @patch('jira.app.sprint_started')
    @patch('jira.app.issue_event')
    @patch('jira.app.q.get')
    def test_issue_event_passed_to_issue_event_func(
        self, mock_q_get, mock_issue_event, mock_sprint_started
    ):
        webhook = {"webhookEvent": "jira:issue_any"}
        mock_q_get.side_effect = [webhook, 'shutdown']
        handle_webhook_from_q()
        mock_issue_event.assert_called_once_with(webhook)
        mock_sprint_started.assert_not_called()

    @patch('jira.app.sprint_started')
    @patch('jira.app.issue_event')
    @patch('jira.app.q.get')
    def test_sprint_started_event_passed_to_sprint_started_func(
        self, mock_q_get, mock_issue_event, mock_sprint_started
    ):
        webhook = {"webhookEvent": "sprint_started"}
        mock_q_get.side_effect = [webhook, 'shutdown']
        handle_webhook_from_q()
        mock_sprint_started.assert_called_once_with(webhook)
        mock_issue_event.assert_not_called()

    @patch('jira.app.sprint_started')
    @patch('jira.app.issue_event')
    @patch('jira.app.q.get')
    def test_other_events_get_discarded(
        self, mock_q_get, mock_issue_event, mock_sprint_started
    ):
        webhook = {"webhookEvent": "jira:other_event"}
        mock_q_get.side_effect = [webhook, 'shutdown']
        handle_webhook_from_q()
        mock_issue_event.assert_not_called()
        mock_sprint_started.assert_not_called()
