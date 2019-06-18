import requests
import unittest
from unittest.mock import patch
from jira import jira
from jira.issues import (
    issue_event, get_parent_issue, get_issues_to_estimate,
    set_backlog_issue_estimate, set_issue_estimates
)


class IssuesTest(unittest.TestCase):

    @patch('jira.issues.get_parent_issue')
    def test_only_correct_project_gets_acted_on(self, mock_get_parent_issue):
        webhook = {
            "issue": {
                "fields": {
                    "issuetype": {
                        "name": "Story",
                        "subtask": False
                    },
                    "project": {
                        "key": "NOT-" + jira.PROJ_KEY
                    }
                }
            }
        }
        issue_event(webhook)
        webhook['issue']['fields']['issuetype']['name'] = "Bug"
        webhook['issue']['fields']['project']['key'] = jira.PROJ_KEY
        issue_event(webhook)
        mock_get_parent_issue.assert_not_called()

    @patch('jira.issues.get_issues_to_estimate')
    @patch('jira.jira.get_issue')
    def test_get_parent_issue_gets_itself_if_story(
        self, mock_get_issue, mock_get_issues_to_estimate
    ):
        mock_get_issue.return_value = {'key': 'TEST-1'}
        get_parent_issue({
            "key": "TEST-1",
            "fields": {
                "issuetype": {
                    "name": "Story",
                    "subtask": False
                }
            }
        })
        mock_get_issue.assert_called_once_with('TEST-1')
        mock_get_issues_to_estimate.assert_called_once_with({'key': 'TEST-1'})

    @patch('jira.issues.get_issues_to_estimate')
    @patch('jira.jira.get_issue')
    def test_get_parent_issue_gets_parent_if_subtask(
        self, mock_get_issue, mock_get_issues_to_estimate
    ):
        mock_get_issue.return_value = {'key': 'TEST-2'}
        get_parent_issue({
            "key": "TEST-1",
            "fields": {
                "issuetype": {
                    "name": "Story Task",
                    "subtask": True
                },
                "parent": {
                    "key": "TEST-2"
                }
            }
        })
        mock_get_issue.assert_called_once_with('TEST-2')
        mock_get_issues_to_estimate.assert_called_once_with({'key': 'TEST-2'})

    @patch('jira.jira.get_issue')
    def test_get_parent_issue_ignores_404_exception(self, mock_get_issue):
        http_error = requests.exceptions.HTTPError()
        http_error.response = requests.Response()
        http_error.response.status_code = 404
        mock_get_issue.side_effect = http_error
        get_parent_issue({
            "key": "TEST-1",
            "fields": {
                "issuetype": {
                    "name": "Story",
                    "subtask": False
                }
            }
        })  # should not raise

    @patch('jira.issues.set_backlog_issue_estimate')
    @patch('jira.issues.set_issue_estimates')
    @patch('jira.jira.get_issues_for_sprint')
    def test_get_issues_to_estimate_sets_backlog_items_to_none(
        self, mock_get_issues_for_sprint, mock_set_issue_estimates,
        mock_set_backlog_issue_estimate
    ):
        get_issues_to_estimate({
            "key": "TEST-1",
            "fields": {
                "sprint": None
            }
        })
        mock_get_issues_for_sprint.assert_not_called()
        mock_set_issue_estimates.assert_not_called()
        mock_set_backlog_issue_estimate.assert_called_once_with("TEST-1")

    @patch('jira.issues.set_backlog_issue_estimate')
    @patch('jira.issues.set_issue_estimates')
    @patch('jira.jira.get_issues_for_sprint')
    def test_get_issues_to_estimate_set_gets_sprint_issues(
        self, mock_get_issues_for_sprint, mock_set_issue_estimates,
        mock_set_backlog_issue_estimate
    ):
        mock_get_issues_for_sprint.return_value = [{'key': 'TEST-1'}]
        get_issues_to_estimate({
            "key": "TEST-1",
            "fields": {
                "sprint": {
                    'id': 1
                }
            }
        })
        mock_set_backlog_issue_estimate.assert_not_called()
        mock_get_issues_for_sprint.assert_called_once_with(1)
        mock_set_issue_estimates.assert_called_once_with([{'key': 'TEST-1'}])

    @patch('jira.jira.update_estimate')
    @patch('jira.jira.get_estimate')
    def test_set_backlog_issue_estimate_does_nothing_if_estimate_is_none(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.return_value = None
        set_backlog_issue_estimate('TEST-1')
        mock_get_estimate.assert_called_once_with('TEST-1')
        mock_update_estimate.assert_not_called()

    @patch('jira.jira.update_estimate')
    @patch('jira.jira.get_estimate')
    def test_set_backlog_issue_estimate_updates_estimate_if_not_none(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.return_value = 5
        set_backlog_issue_estimate('TEST-1')
        mock_get_estimate.assert_called_once_with('TEST-1')
        mock_update_estimate.assert_called_once_with('TEST-1', None)

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
