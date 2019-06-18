import json
import unittest
from unittest.mock import patch
from jira.app import app

app = app.test_client()


class WebhookTest(unittest.TestCase):

    def tearDown(self):
        app.post('/shutdown')

    def test_home_page_returns_correct_html(self):
        response = app.get('/')
        self.assertEqual('JackBot is running!', response.data.decode())

    def test_can_handle_a_post_request(self):
        response = app.post('/', data=json.dumps({"key": 'value'}))
        self.assertEqual(200, response.status_code)

    @patch('jira.app.q.put')
    def test_issue_event_gets_put_in_q(self, mock_q_put, ):
        app.post('/', data=json.dumps({"webhookEvent": "jira:issue_any"}))
        mock_q_put.assert_called_once_with({"webhookEvent": "jira:issue_any"})

    @patch('jira.app.q.put')
    def test_other_events_get_discared(self, mock_q_put, ):
        app.post('/', data=json.dumps({"webhookEvent": "jira:other_event"}))
        mock_q_put.assert_not_called()
