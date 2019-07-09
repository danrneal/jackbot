import unittest
from unittest.mock import patch
from jira import jira
from jira.sprints import (
    sprint_started, get_sprint_issues_by_type, get_message_info,
    get_active_sprint_info
)


class SprintsTest(unittest.TestCase):

    @patch('jira.sprints.get_sprint_issues_by_type')
    def test_incorrect_board_is_ignored(self, mock_get_sprint_issues_by_type):
        sprint_started({
            "sprint": {
                "originBoardId": jira.BOARD_ID + 1
            }
        })
        mock_get_sprint_issues_by_type.assert_not_called()

    @patch('jira.sprints.get_sprint_issues_by_type')
    def test_correct_board_is_acted_on(self, mock_get_sprint_issues_by_type):
        sprint_started({
            "sprint": {
                "id": 1,
                'name': 'TEST Sprint',
                "originBoardId": jira.BOARD_ID
            }
        })
        mock_get_sprint_issues_by_type.assert_called_once_with(1, 'TEST Sprint')

    @patch('jira.sprints.get_sprint_issues_by_type')
    @patch('jira.jira.get_active_sprint')
    def test_get_active_sprint_id_and_name(
            self, mock_get_active_sprint, mock_get_sprint_issues_by_type
    ):
        mock_get_active_sprint.return_value = {
            'id': 1,
            'name': 'TEST Sprint'
        }
        get_active_sprint_info()
        mock_get_sprint_issues_by_type.assert_called_once_with(1, 'TEST Sprint')

    @patch('jira.sprints.get_message_info')
    @patch('jira.jira.get_issues_for_sprint')
    def test_get_sprint_issues_by_type_ignores_done_issues(
        self, mock_get_issues_for_sprint, mock_add_issue_estimates
    ):
        mock_get_issues_for_sprint.return_value = [{
            'fields': {
                'status': {
                    "statusCategory": {
                        "name": "Done"
                    }
                }
            }
        }]
        get_sprint_issues_by_type(1, 'TEST Sprint')
        mock_add_issue_estimates.assert_called_once_with('TEST Sprint', [])

    @patch('jira.sprints.get_message_info')
    @patch('jira.jira.get_issues_for_sprint')
    def test_get_sprint_issues_by_type_does_not_include_stories_in_burndown(
        self, mock_get_issues_for_sprint, mock_add_issue_estimates
    ):
        mock_get_issues_for_sprint.return_value = [{
            'fields': {
                'issuetype': {
                    'name': 'Story'
                },
                'status': {
                    "statusCategory": {
                        "name": "Not Done"
                    }
                }
            }
        }]
        get_sprint_issues_by_type(1, 'TEST Sprint')
        mock_add_issue_estimates.assert_called_once_with('TEST Sprint', [])

    @patch('jira.sprints.get_message_info')
    @patch('jira.jira.get_issues_for_sprint')
    def test_get_sprint_issues_by_type_includes_non_stories_in_burndown(
        self, mock_get_issues_for_sprint, mock_add_issue_estimates
    ):
        mock_get_issues_for_sprint.return_value = [{
            'key': 'TEST-1',
            'fields': {
                'issuetype': {
                    'name': 'Bug'
                },
                'status': {
                    "statusCategory": {
                        "name": "In Progress"
                    }
                }
            }
        }]
        get_sprint_issues_by_type(1, 'TEST Sprint')
        mock_add_issue_estimates.assert_called_once_with('TEST Sprint', [{
            'key': 'TEST-1',
            'type': 'bug'
        }])

    @patch('slack.webhooks.build_message')
    @patch('jira.jira.get_estimate')
    def test_issue_estimates_are_added_up(
        self, mock_get_estimate, mock_build_message
    ):
        mock_get_estimate.side_effect = [2, 8]
        get_message_info('TEST Sprint', [
            {
                'key': 'TEST-1',
                'type': 'Story Task'
            },
            {
                'key': 'TEST-2',
                'type': 'Story Task'
            }
        ])
        mock_build_message.assert_called_once_with({
            'name': 'TEST Sprint',
            'burndown': 10
        }, [])

    @patch('slack.webhooks.build_message')
    @patch('jira.jira.get_estimate')
    def test_missing_estimate_issues_are_passed_along(
        self, mock_get_estimate, mock_build_message
    ):
        mock_get_estimate.side_effect = [None]
        get_message_info('TEST Sprint', [
            {
                'key': 'TEST-1',
                'type': 'Bug'
            }
        ])
        mock_build_message.assert_called_once_with(
            {
                'name': 'TEST Sprint',
                'burndown': 0
            },
            [{
                'key': 'TEST-1',
                'type': 'Bug'
            }]
        )
