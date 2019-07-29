import json
import unittest
from unittest.mock import patch, Mock
from jira import jira


class JiraTest(unittest.TestCase):

    @patch('requests.request')
    def test_get_active_sprint(self, mock_request):
        mock_request.return_value = Mock()
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = (
            '{"values": [{"state": "closed"}, {"state": "active"}]}'
        )
        sprint = jira.get_active_sprint()
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}/rest/agile/1.0/board/{jira.BOARD_ID}/sprint",
            data=None,
            headers=jira.headers
        )
        self.assertEqual(sprint, {"state": "active"})

    @patch('requests.request')
    def test_get_active_sprint_discards_inactive_sprints(self, mock_request):
        mock_request.return_value = Mock()
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = '{"values": [{"state": "closed"}]}'
        sprint = jira.get_active_sprint()
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}/rest/agile/1.0/board/{jira.BOARD_ID}/sprint",
            data=None,
            headers=jira.headers
        )
        self.assertEqual(sprint, None)

    @patch('requests.request')
    def test_get_issues_for_sprint(self, mock_request):
        mock_request.return_value = Mock()
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps({
            'maxResults': 50,
            'startAt': 0,
            'total': 1,
            'issues': [{"key": "TEST-1"}]
        })
        sprint_issues = jira.get_issues_for_sprint(1)
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}/rest/agile/1.0/sprint/1/issue",
            data=None,
            headers=jira.headers
        )
        self.assertEqual([{"key": "TEST-1"}], sprint_issues)

    @patch('requests.request')
    def test_get_issues_for_sprint_paginates_when_necessary(self, mock_request):
        sprint_issues_page_1 = Mock()
        sprint_issues_page_1.status_code = 200
        sprint_issues_page_1.text = json.dumps({
            'maxResults': 50,
            'startAt': 0,
            'total': 51,
            'issues': [{"key": "TEST-1"}]
        })
        sprint_issues_page_2 = Mock()
        sprint_issues_page_2.status_code = 200
        sprint_issues_page_2.text = json.dumps({
            'maxResults': 50,
            'startAt': 50,
            'total': 51,
            'issues': [{"key": "TEST-2"}]
        })
        mock_request.side_effect = [sprint_issues_page_1, sprint_issues_page_2]
        sprint_issues = jira.get_issues_for_sprint(1)
        mock_request.assert_any_call(
            "GET", f"{jira.SERVER}/rest/agile/1.0/sprint/1/issue",
            data=None,
            headers=jira.headers
        )
        mock_request.assert_called_with(
            "GET", f"{jira.SERVER}/rest/agile/1.0/sprint/1/issue?startAt=50",
            data=None,
            headers=jira.headers
        )
        self.assertEqual([{"key": "TEST-1"}, {"key": "TEST-2"}], sprint_issues)

    @patch('requests.request')
    def test_get_issue(self, mock_request):
        mock_request.return_value = Mock()
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = '{"key": "TEST-1"}'
        issue = jira.get_issue('TEST-1')
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}/rest/agile/1.0/issue/TEST-1",
            data=None,
            headers=jira.headers
        )
        self.assertEqual({"key": "TEST-1"}, issue)

    @patch('requests.request')
    def test_get_estimate(self, mock_request):
        mock_request.return_value = Mock()
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = '{"value": 11}'
        estimate = jira.get_estimate('TEST-1')
        endpoint = "/rest/agile/1.0/issue/TEST-1/estimation"
        query = f"boardId={jira.BOARD_ID}"
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}{endpoint}?{query}",
            data=None,
            headers=jira.headers
        )
        self.assertEqual(11, estimate)

    @patch('requests.request')
    def test_update_estimate(self, mock_request):
        mock_request.return_value = Mock()
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = ''
        jira.update_estimate('TEST-1', 11)
        endpoint = "/rest/agile/1.0/issue/TEST-1/estimation"
        query = f"boardId={jira.BOARD_ID}"
        mock_request.assert_called_once_with(
            "PUT", f"{jira.SERVER}{endpoint}?{query}",
            data='{"value": 11}',
            headers=jira.headers
        )
