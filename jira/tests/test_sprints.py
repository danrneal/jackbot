import unittest
from unittest.mock import patch
from jira import jira
from jira.sprints import (
    sprint_started, get_burndown_issues, add_issue_estimates,
    get_active_sprint_info
)


class SprintsTest(unittest.TestCase):

    @patch('jira.sprints.get_burndown_issues')
    def test_incorrect_board_is_ignored(self, mock_get_burndown_issues):
        sprint_started({
            "sprint": {
                "originBoardId": jira.BOARD_ID + 1
            }
        })
        mock_get_burndown_issues.assert_not_called()

    @patch('jira.sprints.get_burndown_issues')
    def test_correct_board_is_acted_on(self, mock_get_burndown_issues):
        sprint_started({
            "sprint": {
                "id": 1,
                'name': 'TEST Sprint',
                "originBoardId": jira.BOARD_ID
            }
        })
        mock_get_burndown_issues.assert_called_once_with(1, 'TEST Sprint')

    @patch('jira.sprints.add_issue_estimates')
    @patch('jira.jira.get_issues_for_sprint')
    def test_get_burndown_issues_gets_all_undone_issues_and_no_stories(
        self, mock_get_issues_for_sprint, mock_add_issue_estimates
    ):
        issue_1 = {
            'key': 'TEST-1',
            'fields': {
                'issuetype': {
                    'name': 'Story Task'
                },
                'status': {
                    "statusCategory": {
                        "name": "Done"
                    }
                }
            }
        }
        issue_2 = {
            'key': 'TEST-2',
            'fields': {
                'issuetype': {
                    'name': 'Story Task'
                },
                'status': {
                    "statusCategory": {
                        "name": "In Progress"
                    }
                }
            }
        }
        issue_3 = {
            'key': 'TEST-3',
            'fields': {
                'issuetype': {
                    'name': 'Story'
                },
                'status': {
                    "statusCategory": {
                        "name": "In Progress"
                    }
                }
            }
        }
        mock_get_issues_for_sprint.return_value = [issue_1, issue_2, issue_3]
        get_burndown_issues(1, 'TEST Sprint')
        mock_add_issue_estimates.assert_called_once_with(
            ['TEST-2'], 'TEST Sprint'
        )

    @patch('slack.webhooks.build_message')
    @patch('jira.jira.get_estimate')
    def test_issue_estimates_are_added_up(
        self, mock_get_estimate, mock_build_message
    ):
        mock_get_estimate.side_effect = [2, None, 8]
        add_issue_estimates(['TEST-1', 'TEST-2', 'TEST-3'], 'TEST Sprint')
        mock_build_message.assert_called_once_with(10, 'TEST Sprint')

    @patch('jira.sprints.get_burndown_issues')
    @patch('jira.jira.get_active_sprint')
    def test_get_active_sprint_id_and_name(
            self, mock_get_active_sprint, mock_get_burndown_issues
    ):
        mock_get_active_sprint.return_value = {
            'id': 1,
            'name': 'TEST Sprint'
        }
        get_active_sprint_info()
        mock_get_burndown_issues.assert_called_once_with(1, 'TEST Sprint')
