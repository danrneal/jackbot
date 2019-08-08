import unittest
from unittest.mock import patch
from jira import jira
from jira.sprints import (
    sprint_event, get_sprint_issues_by_type, get_message_info,
    get_active_sprint_info
)


@patch('jira.sprints.get_sprint_issues_by_type')
class SprintsTest(unittest.TestCase):

    sprint = {
        "id": 1,
        "name": 'TEST Sprint',
    }

    def test_incorrect_board_is_ignored(self, mock_get_sprint_issues_by_type):
        self.sprint['originBoardId'] = jira.BOARD_ID + 1
        sprint_event(self.sprint)
        mock_get_sprint_issues_by_type.assert_not_called()

    def test_correct_board_is_acted_on(self, mock_get_sprint_issues_by_type):
        self.sprint['originBoardId'] = jira.BOARD_ID
        sprint_event(self.sprint)
        mock_get_sprint_issues_by_type.assert_called_once_with(1, 'TEST Sprint')


class GetActiveSprintInfo(unittest.TestCase):

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

    @patch('jira.sprints.get_sprint_issues_by_type')
    @patch('jira.jira.get_active_sprint')
    def test_get_active_sprint_info_returns_when_there_is_no_active_sprint(
        self, mock_get_active_sprint, mock_get_sprint_issues_by_type
    ):
        mock_get_active_sprint.return_value = None
        get_active_sprint_info()
        mock_get_sprint_issues_by_type.assert_not_called()


@patch('jira.sprints.get_message_info')
@patch('jira.jira.get_issues_for_sprint')
class GetSprintIssueByType(unittest.TestCase):

    issue_1 = {
        'key': 'TEST-1',
        'fields': {
            'issuetype': {},
            'status': {
                "statusCategory": {}
            },
            'assignee': None,
            'subtasks': []
        }
    }

    issue_2 = {
        'key': 'TEST-2',
        'fields': {
            'issuetype': {},
            'status': {
                "statusCategory": {}
            },
            'assignee': None,
            'subtasks': []
        }
    }

    def test_ignores_done_issues(
        self, mock_get_issues_for_sprint, mock_get_message_info
    ):
        self.issue_1['fields']['status']['statusCategory']['name'] = 'Done'
        mock_get_issues_for_sprint.return_value = [self.issue_1]
        get_sprint_issues_by_type(1, 'TEST Sprint')
        mock_get_message_info.assert_called_once_with('TEST Sprint', [], [], [])

    def test_ignores_stories_with_subtasks(
        self, mock_get_issues_for_sprint, mock_get_message_info
    ):
        self.issue_1['fields']['issuetype'] = {'name': "Story"}
        self.issue_1['fields']['status']['statusCategory']['name'] = 'Not Done'
        self.issue_1['fields']['subtasks'].append({'key': 'TEST-3'})
        mock_get_issues_for_sprint.return_value = [self.issue_1]
        get_sprint_issues_by_type(1, 'TEST Sprint')
        mock_get_message_info.assert_called_once_with('TEST Sprint', [], [], [])

    def test_separates_stories_wo_subtasks(
        self, mock_get_issues_for_sprint, mock_get_message_info
    ):
        self.issue_1['fields']['issuetype'] = {'name': "Story"}
        self.issue_1['fields']['status']['statusCategory']['name'] = 'Not Done'
        self.issue_1['fields']['subtasks'].clear()
        self.issue_1['fields']['assignee'] = None
        mock_get_issues_for_sprint.return_value = [self.issue_1]
        get_sprint_issues_by_type(1, 'TEST Sprint')
        mock_get_message_info.assert_called_once_with('TEST Sprint', [{
            'key': 'TEST-1',
            'type': 'story',
            'assignee': None
        }], [], [])

    def test_get_sprint_issuses_by_type_passes_assignee_when_exists(
        self, mock_get_issues_for_sprint, mock_get_message_info
    ):
        self.issue_1['fields']['issuetype'] = {'name': "Story"}
        self.issue_1['fields']['status']['statusCategory']['name'] = 'Not Done'
        self.issue_1['fields']['subtasks'].clear()
        self.issue_1['fields']['assignee'] = {'displayName': 'someone'}
        mock_get_issues_for_sprint.return_value = [self.issue_1]
        get_sprint_issues_by_type(1, 'TEST Sprint')
        mock_get_message_info.assert_called_once_with('TEST Sprint', [{
            'key': 'TEST-1',
            'type': 'story',
            'assignee': 'someone'
        }], [], [])

    def test_get_sprint_issues_by_type_separates_out_bugs(
        self, mock_get_issues_for_sprint, mock_get_message_info
    ):
        self.issue_1['fields']['issuetype'] = {'name': "Bug"}
        self.issue_1['fields']['status']['statusCategory']['name'] = "Not Done"
        self.issue_1['fields']['assignee'] = None
        self.issue_2['fields']['issuetype'] = {'name': "Critical"}
        self.issue_2['fields']['status']['statusCategory']['name'] = "Not Done"
        self.issue_2['fields']['assignee'] = None
        mock_get_issues_for_sprint.return_value = [self.issue_1, self.issue_2]
        get_sprint_issues_by_type(1, 'TEST Sprint')
        mock_get_message_info.assert_called_once_with('TEST Sprint', [], [
            {
                'key': 'TEST-1',
                'type': 'bug',
                'assignee': None
            },
            {
                'key': 'TEST-2',
                'type': 'bug',
                'assignee': None
            },
        ], [])

    def test_get_sprint_issues_by_type_separates_out_tasks(
        self, mock_get_issues_for_sprint, mock_get_message_info
    ):
        self.issue_1['fields']['issuetype'] = {'name': "Task"}
        self.issue_1['fields']['status']['statusCategory']['name'] = "Not Done"
        self.issue_1['fields']['assignee'] = None
        self.issue_2['fields']['issuetype'] = {'name': "Story Task"}
        self.issue_2['fields']['status']['statusCategory']['name'] = "Not Done"
        self.issue_2['fields']['assignee'] = None
        mock_get_issues_for_sprint.return_value = [self.issue_1, self.issue_2]
        get_sprint_issues_by_type(1, 'TEST Sprint')
        mock_get_message_info.assert_called_once_with('TEST Sprint', [], [], [
            {
                'key': 'TEST-1',
                'type': 'task',
                'assignee': None
            },
            {
                'key': 'TEST-2',
                'type': 'task',
                'assignee': None
            },
        ])


@patch('slack.webhooks.build_message')
@patch('jira.jira.get_estimate')
class GetMessageInfoTest(unittest.TestCase):

    issue = {}

    sprint_info = {
        'name': 'TEST Sprint',
        'burndown': 0
    }

    def test_issue_estimates_are_added_up(
        self, mock_get_estimate, mock_build_message
    ):
        self.issue['key'] = 'TEST-1'
        self.issue['type'] = 'task'
        self.issue['key'] = 'someone'
        mock_get_estimate.side_effect = [2, 8]
        get_message_info('TEST Sprint', [], [], [self.issue, self.issue])
        self.sprint_info['burndown'] = 10
        mock_build_message.assert_called_once_with(self.sprint_info, [], [], [])

    def test_missing_estimate_issues_are_passed_along(
        self, mock_get_estimate, mock_build_message
    ):
        self.issue['key'] = 'TEST-1'
        self.issue['type'] = 'bug'
        self.issue['key'] = 'someone'
        mock_get_estimate.return_value = None
        get_message_info('TEST Sprint', [], [self.issue], [])
        self.sprint_info['burndown'] = 0
        mock_build_message.assert_called_once_with(
            self.sprint_info, [], [self.issue], []
        )

    def test_large_estimate_issues_are_passed_along(
        self, mock_get_estimate, mock_build_message
    ):
        self.issue['key'] = 'TEST-1'
        self.issue['type'] = 'task'
        self.issue['key'] = 'someone'
        mock_get_estimate.return_value = 17
        get_message_info('TEST Sprint', [], [], [self.issue])
        self.sprint_info['burndown'] = 17
        mock_build_message.assert_called_once_with(
            self.sprint_info, [], [], [self.issue]
        )
