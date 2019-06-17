import json
import unittest
from unittest.mock import patch
from jira.app import app

app = app.test_client()


class WebhookTest(unittest.TestCase):

    def test_home_page_returns_correct_html(self):
        response = app.get('/')
        self.assertEqual('JackBot is running!', response.data.decode())

    def test_can_handle_a_post_request(self):
        response = app.post('/', data=json.dumps({"key": 'value'}))
        self.assertEqual(200, response.status_code)

    @patch('jira.app.issue_event')
    def test_issue_event_gets_passed_to_issue_event_function(
        self, mock_issue_event
    ):
        app.post('/', data=json.dumps({"webhookEvent": "jira:issue_anything"}))
        mock_issue_event.assert_called_once_with({
            "webhookEvent": "jira:issue_anything"}
        )

    @patch('jira.app.issue_event')
    def test_other_events_get_discared(self, mock_issue_event):
        app.post('/', data=json.dumps({"webhookEvent": "jira:other_event"}))
        mock_issue_event.assert_not_called()
