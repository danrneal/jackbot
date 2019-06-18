import requests
import unittest
from unittest.mock import patch
from jira import jira
from jira.issues import (
    issue_event, get_issue_sprint, get_sprint_stories,
    set_backlog_issue_estimate, set_issue_estimates
)


class IssuesTest(unittest.TestCase):

    @patch('jira.issues.get_issue_sprint')
    @patch('jira.issues.q.get')
    def test_incorrect_project_is_ignored(
        self, mock_q_get, mock_get_issue_sprint
    ):
        mock_q_get.return_value = {
            "issue": {
                "fields": {
                    "project": {
                        "key": "NOT-" + jira.PROJ_KEY
                    }
                }
            }
        }
        issue_event()
        mock_get_issue_sprint.assert_not_called()

    @patch('jira.issues.get_issue_sprint')
    @patch('jira.issues.q.get')
    def test_correct_project_is_acted_on(
        self, mock_q_get, mock_get_issue_sprint
    ):
        mock_q_get.side_effect = [{
            "issue": {
                "key": "TEST-1",
                "fields": {
                    "project": {
                        "key": jira.PROJ_KEY
                    }
                }
            }
        }, None]
        issue_event()
        mock_get_issue_sprint.assert_called_once_with("TEST-1")

    @patch('jira.issues.get_sprint_stories')
    @patch('jira.issues.set_backlog_issue_estimate')
    @patch('jira.jira.get_issue')
    def test_get_issue_sprint_gets_issue_sprint(
        self, mock_get_issue, mock_set_backlog_issue_estimate,
            mock_get_sprint_stories
    ):
        mock_get_issue.return_value = {
            "key": "TEST-1",
            "fields": {
                "sprint": {
                    "id": 1
                }
            }
        }
        get_issue_sprint("TEST-1")
        mock_set_backlog_issue_estimate.assert_not_called()
        mock_get_sprint_stories.assert_called_once_with(1)

    @patch('jira.issues.get_sprint_stories')
    @patch('jira.issues.set_backlog_issue_estimate')
    @patch('jira.jira.get_issue')
    def test_get_issue_sprint_deals_with_backlogged_items(
        self, mock_get_issue, mock_set_backlog_issue_estimate,
            mock_get_sprint_stories
    ):
        issue = {
            "key": "TEST-1",
            "fields": {
                "sprint": None
            }
        }
        mock_get_issue.return_value = issue
        get_issue_sprint("TEST-1")
        mock_get_sprint_stories.assert_not_called()
        mock_set_backlog_issue_estimate.assert_called_once_with(issue)

    @patch('jira.jira.get_issue')
    def test_get_issue_sprint_ignores_404_exception(self, mock_get_issue):
        http_error = requests.exceptions.HTTPError()
        http_error.response = requests.Response()
        http_error.response.status_code = 404
        mock_get_issue.side_effect = http_error
        get_issue_sprint("TEST-1")  # should not raise

    @patch('jira.jira.update_estimate')
    @patch('jira.jira.get_estimate')
    def test_set_backlog_issue_estimate_gets_parent_of_subtask(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.return_value = 3
        set_backlog_issue_estimate({
            'fields': {
                "parent": {
                    'key': "TEST-1"
                }
            }
        })
        mock_get_estimate.assert_called_once_with("TEST-1")
        mock_update_estimate.assert_called_once_with("TEST-1", None)

    @patch('jira.jira.update_estimate')
    @patch('jira.jira.get_estimate')
    def test_set_backlog_issue_estimate_gets_own_estimate_if_not_subtask(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.return_value = None
        set_backlog_issue_estimate({
            'key': 'TEST-1',
            'fields': {}
        })
        mock_get_estimate.assert_called_once_with("TEST-1")
        mock_update_estimate.assert_not_called()

    @patch('jira.issues.set_issue_estimates')
    @patch('jira.jira.get_issues_for_sprint')
    def test_get_sprint_stories_only_gets_stories(
        self, mock_get_issues_for_sprint, mock_set_issue_estimates
    ):
        issue_1 = {
            'fields': {
                'issuetype': {
                    'name': 'Bug'
                }
            }
        }
        issue_2 = {
            'fields': {
                'issuetype': {
                    'name': 'Story'
                }
            }
        }
        mock_get_issues_for_sprint.return_value = [issue_1, issue_2]
        get_sprint_stories(1)
        mock_set_issue_estimates.assert_called_once_with([issue_2])

    @patch('jira.jira.update_estimate')
    @patch('jira.jira.get_estimate')
    def test_set_issue_estimates_update_issue_estimates(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.side_effect = [2, 5, 7, None, 8, 11]
        set_issue_estimates([
            {
                "key": "TEST-1",
                "fields": {
                    "subtasks": [{"key": "TEST-3"}, {"key": "TEST-4"}]
                }
            },
            {
                "key": "TEST-2",
                'fields': {
                    "subtasks": [{"key": "TEST-5"}, {"key": "TEST-6"}]
                }
            },
        ])
        mock_get_estimate.assert_any_call("TEST-3")
        mock_get_estimate.assert_any_call("TEST-4")
        mock_get_estimate.assert_any_call("TEST-1")
        mock_get_estimate.assert_any_call("TEST-5")
        mock_get_estimate.assert_any_call("TEST-6")
        mock_get_estimate.assert_any_call("TEST-2")
        mock_update_estimate.assert_called_once_with("TEST-2", 8)
