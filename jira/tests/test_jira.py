import json
import unittest
from unittest.mock import patch, Mock
from jira import jira


@patch('requests.request')
class JiraTest(unittest.TestCase):

    @staticmethod
    def create_mock_request(mock_request, response=None):
        mock_request.return_value = Mock()
        mock_request.return_value.status_code = 200
        mock_request.return_value.text = json.dumps(response)
        return mock_request.return_value

    def test_get_active_sprint(self, mock_request):
        self.create_mock_request(mock_request, {
            'values': [
                {
                    'state': 'closed'
                },
                {
                    'state': 'active'
                }
            ]
        })
        sprint = jira.get_active_sprint()
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}/rest/agile/1.0/board/{jira.BOARD_ID}/sprint",
            data=None,
            headers=jira.headers
        )
        self.assertEqual(sprint, {"state": "active"})

    def test_get_active_sprint_discards_inactive_sprints(self, mock_request):
        self.create_mock_request(mock_request, {
            'values': [
                {
                    'state': 'closed'
                }
            ]
        })
        sprint = jira.get_active_sprint()
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}/rest/agile/1.0/board/{jira.BOARD_ID}/sprint",
            data=None,
            headers=jira.headers
        )
        self.assertEqual(sprint, None)

    def test_get_issues_for_sprint(self, mock_request):
        self.create_mock_request(mock_request, {
            'maxResults': 50,
            'startAt': 0,
            'total': 1,
            'issues': [{
                "key": "TEST-1"
            }]
        })
        sprint_issues = jira.get_issues_for_sprint(1)
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}/rest/agile/1.0/sprint/1/issue",
            data=None,
            headers=jira.headers
        )
        self.assertEqual([{"key": "TEST-1"}], sprint_issues)

    def test_get_issues_for_sprint_paginates_when_necessary(self, mock_request):
        sprint_issues_page_1 = self.create_mock_request(mock_request, {
            'maxResults': 50,
            'startAt': 0,
            'total': 51,
            'issues': [{
                "key": "TEST-1"
            }]
        })
        sprint_issues_page_2 = self.create_mock_request(mock_request, {
            'maxResults': 50,
            'startAt': 50,
            'total': 51,
            'issues': [{
                "key": "TEST-2"
            }]
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

    def test_get_issue(self, mock_request):
        self.create_mock_request(mock_request, {'key': 'TEST-1'})
        issue = jira.get_issue('TEST-1')
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}/rest/agile/1.0/issue/TEST-1",
            data=None,
            headers=jira.headers
        )
        self.assertEqual({"key": "TEST-1"}, issue)

    def test_get_estimate(self, mock_request):
        self.create_mock_request(mock_request, {'value': 11})
        estimate = jira.get_estimate('TEST-1')
        endpoint = "/rest/agile/1.0/issue/TEST-1/estimation"
        query = f"boardId={jira.BOARD_ID}"
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}{endpoint}?{query}",
            data=None,
            headers=jira.headers
        )
        self.assertEqual(11, estimate)

    def test_update_estimate(self, mock_request):
        self.create_mock_request(mock_request)
        jira.update_estimate('TEST-1', 11)
        endpoint = "/rest/agile/1.0/issue/TEST-1/estimation"
        query = f"boardId={jira.BOARD_ID}"
        mock_request.assert_called_once_with(
            "PUT", f"{jira.SERVER}{endpoint}?{query}",
            data=json.dumps({"value": 11}),
            headers=jira.headers
        )

    def test_assign_issue(self, mock_request):
        self.create_mock_request(mock_request)
        jira.assign_issue('TEST-1', None)
        mock_request.assert_called_once_with(
            "PUT", f"{jira.SERVER}/rest/api/3/issue/TEST-1/assignee",
            data=json.dumps({"accountId": None}),
            headers=jira.headers
        )

    def test_get_transition_id(self, mock_request):
        self.create_mock_request(mock_request, {
            'transitions': [
                {
                    "name": "Wrong Transition",
                    "id": 1
                },
                {
                    "name": "Right Transition",
                    'id': 2
                }
            ]
        })
        transition_id = jira.get_transition_id('TEST-1', 'Right Transition')
        mock_request.assert_called_once_with(
            "GET", f"{jira.SERVER}/rest/api/3/issue/TEST-1/transitions",
            data=None,
            headers=jira.headers
        )
        self.assertEqual(2, transition_id)

    @patch('jira.jira.get_transition_id')
    def test_transition_issue(self, mock_get_transition_id, mock_request):
        mock_get_transition_id.return_value = 1
        self.create_mock_request(mock_request)
        jira.transition_issue('TEST-1', 'Test Transition')
        mock_request.assert_called_once_with(
            "POST", f"{jira.SERVER}/rest/api/3/issue/TEST-1/transitions",
            data=json.dumps({
                "transition": {
                    "id": 1
                }
            }),
            headers=jira.headers
        )
