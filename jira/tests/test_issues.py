import requests
import unittest
from unittest.mock import patch
from jira import jira
from jira.issues import (
    issue_event, get_issue_sprint, round_sprint_issue_estimates,
    get_sprint_stories, set_story_status, set_story_estimate,
    get_backlog_parent_issue, set_backlog_parent_issue_status,
    set_backlog_parent_issue_assignee, set_backlog_parent_issue_estimate
)


@patch('jira.issues.get_issue_sprint')
class IssueEventTest(unittest.TestCase):

    data = {
        "issue": {
            "key": "TEST-1",
            "fields": {
                "project": {
                    "key": None
                }
            }
        }
    }

    def test_correct_project_is_acted_on(self, mock_get_issue_sprint):
        self.data['issue']['fields']['project']['key'] = jira.PROJ_KEY
        issue_event(self.data)
        mock_get_issue_sprint.assert_called_once_with("TEST-1")

    def test_incorrect_project_is_ignored(self, mock_get_issue_sprint):
        self.data['issue']['fields']['project']['key'] = 'NOT' + jira.PROJ_KEY
        issue_event(self.data)
        mock_get_issue_sprint.assert_not_called()


@patch('jira.issues.get_backlog_parent_issue')
@patch('jira.issues.round_sprint_issue_estimates')
@patch('jira.jira.get_issue')
class GetIssueSprintTest(unittest.TestCase):

    issue = {
        "key": "TEST-1",
        "fields": {}
    }

    http_404_error = requests.exceptions.HTTPError()
    http_404_error.response = requests.Response()
    http_404_error.response.status_code = 404

    def test_gets_issue_sprint(
        self, mock_get_issue, mock_round_sprint_issue_estimates,
        mock_get_backlog_parent_issue
    ):
        self.issue['fields']['sprint'] = {"id": 1}
        mock_get_issue.return_value = self.issue
        get_issue_sprint("TEST-1")
        mock_round_sprint_issue_estimates.assert_called_once_with(1)
        mock_get_backlog_parent_issue.assert_not_called()

    def test_deals_with_backlogged_items(
        self, mock_get_issue, mock_round_sprint_issue_estimates,
        mock_get_backlog_parent_issue
    ):
        self.issue['fields']['sprint'] = None
        mock_get_issue.return_value = self.issue
        get_issue_sprint("TEST-1")
        mock_round_sprint_issue_estimates.assert_not_called()
        mock_get_backlog_parent_issue.assert_called_once_with(self.issue)

    def test_ignores_404_exception(
        self, mock_get_issue, mock_round_sprint_issue_estimates,
        mock_get_backlog_parent_issue
    ):
        mock_get_issue.side_effect = self.http_404_error
        get_issue_sprint("TEST-1")  # should not raise
        mock_round_sprint_issue_estimates.assert_not_called()
        mock_get_backlog_parent_issue.assert_not_called()


@patch('jira.issues.get_sprint_stories')
@patch('jira.jira.update_estimate')
@patch('jira.jira.get_estimate')
@patch('jira.jira.get_issues_for_sprint')
class RoundSprintIssueEstimatesTest(unittest.TestCase):

    sprint_issues = [{
        'key': 'TEST-1',
        'fields': {
            'issuetype': {
                'name': 'Bug'
            }
        }
    }]

    def test_rounds_up_fractional_estimates(
        self, mock_get_issues_for_sprint, mock_get_estimate,
        mock_update_estimate, mock_get_sprint_story_subtasks
    ):
        mock_get_issues_for_sprint.return_value = self.sprint_issues
        mock_get_estimate.return_value = 7.2
        round_sprint_issue_estimates(1)
        mock_update_estimate.assert_called_once_with('TEST-1', 8)
        mock_get_sprint_story_subtasks.assert_called_once_with(
            self.sprint_issues
        )

    def test_ignores_integer_estimates(
        self, mock_get_issues_for_sprint, mock_get_estimate,
        mock_update_estimate, mock_get_sprint_story_subtasks
    ):
        mock_get_issues_for_sprint.return_value = self.sprint_issues
        mock_get_estimate.return_value = 5
        round_sprint_issue_estimates(1)
        mock_update_estimate.assert_not_called()
        mock_get_sprint_story_subtasks.assert_called_once_with(
            self.sprint_issues
        )


@patch('jira.issues.set_story_estimate')
@patch('jira.issues.set_story_status')
class GetSprintStoriesTest(unittest.TestCase):

    sprint_issues = [{
        'key': 'TEST-1',
        'fields': {
            'issuetype': {},
            'subtasks': []
        }
    }]

    def test_gets_stories(self, mock_set_story_status, mock_set_story_estimate):
        self.sprint_issues[0]['fields']['issuetype']['name'] = 'Story'
        get_sprint_stories(self.sprint_issues)
        mock_set_story_status.assert_called_once_with(self.sprint_issues[0])
        mock_set_story_estimate.assert_called_once_with(self.sprint_issues[0])

    def test_ignores_non_stories(
        self, mock_set_story_status, mock_set_story_estimate
    ):
        self.sprint_issues[0]['fields']['issuetype']['name'] = 'Bug'
        get_sprint_stories(self.sprint_issues)
        mock_set_story_status.assert_not_called()
        mock_set_story_estimate.assert_not_called()

    def test_ignores_archived_subtasks(
        self, mock_set_story_status, mock_set_story_estimate
    ):
        self.sprint_issues[0]['fields']['issuetype']['name'] = 'Story'
        self.sprint_issues[0]['fields']['subtasks'].append({
            'fields': {
                'status': {
                    'name': 'Archive'
                }
            }
        })
        get_sprint_stories(self.sprint_issues)
        self.sprint_issues[0]['fields']['subtasks'].clear()
        mock_set_story_status.assert_called_once_with(self.sprint_issues[0])
        mock_set_story_estimate.assert_called_once_with(self.sprint_issues[0])


@patch('jira.jira.transition_issue')
class SetStoryStatusTest(unittest.TestCase):

    story = {
        "key": "TEST-1",
        "fields": {
            "status": {},
            "subtasks": []
        }
    }

    subtask = {
        "fields": {
            "status": {}
        }
    }

    def test_sets_backlog_as_default_status(self, mock_transition_issue):
        self.story['fields']['status']['name'] = 'Not Backlog'
        self.story['fields']['subtasks'].clear()
        set_story_status(self.story)
        mock_transition_issue.assert_called_once_with("TEST-1", "Backlog")

    def test_bocklogs_issue_when_all_subtasks_are_backlog(
        self, mock_transition_issue
    ):
        self.story['fields']['status']['name'] = 'Not Backlog'
        self.subtask['fields']['status']['name'] = 'Backlog'
        self.story['fields']['subtasks'].append(self.subtask)
        set_story_status(self.story)
        mock_transition_issue.assert_called_once_with("TEST-1", "Backlog")

    def test_set_story_status_sets_status_to_po_review_when_all_subtasks_done(
        self, mock_transition_issue
    ):
        self.story['fields']['status']['name'] = 'Not PO Review'
        self.subtask['fields']['status']['name'] = 'Done'
        self.story['fields']['subtasks'].append(self.subtask)
        set_story_status(self.story)
        mock_transition_issue.assert_called_once_with("TEST-1", "PO Review")

    def test_set_story_status_ignores_done_issues_when_all_subtasks_done(
        self, mock_transition_issue
    ):
        self.story['fields']['status']['name'] = 'Done'
        self.subtask['fields']['status']['name'] = 'Done'
        self.story['fields']['subtasks'].append(self.subtask)
        set_story_status(self.story)
        mock_transition_issue.assert_not_called()

    def test_set_story_status_sets_status_to_in_progress_when_appropriate(
        self, mock_transition_issue
    ):
        self.story['fields']['status']['name'] = 'Not In Progress'
        self.subtask['fields']['status']['name'] = 'Not Done'
        self.story['fields']['subtasks'].append(self.subtask)
        self.story['fields']['subtasks'].append({
            "fields": {
                "status": {
                    "name": "Done"
                }
            }
        })
        set_story_status(self.story)
        mock_transition_issue.assert_called_once_with("TEST-1", "In Progress")

    def test_set_story_status_ignores_correct_status(
        self, mock_transition_issue
    ):
        self.story['fields']['status']['name'] = 'Backlog'
        self.story['fields']['subtasks'].clear()
        set_story_status(self.story)
        mock_transition_issue.assert_not_called()


@patch('jira.jira.update_estimate')
@patch('jira.jira.get_estimate')
class SetStoryEstimateTest(unittest.TestCase):

    story = {
        "key": "TEST-1",
        "fields": {
            "subtasks": [
                {
                    "key": "TEST-2"
                },
                {
                    "key": "TEST-3"
                }
            ]
        }
    }

    def test_adds_up_issues_correctly(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.side_effect = [None, 2, 5]
        set_story_estimate(self.story)
        mock_update_estimate.assert_called_once_with("TEST-1", 7)

    def test_ignores_missing_estimates(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.side_effect = [11, 8, None]
        set_story_estimate(self.story)
        mock_update_estimate.assert_called_once_with("TEST-1", 8)

    def test_ignores_correct_estimates(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.side_effect = [11, 8, 3]
        set_story_estimate(self.story)
        mock_update_estimate.assert_not_called()


@patch('jira.issues.set_backlog_parent_issue_estimate')
@patch('jira.issues.set_backlog_parent_issue_assignee')
@patch('jira.issues.set_backlog_parent_issue_status')
@patch('jira.jira.get_issue')
class GetBacklogParentIssue(unittest.TestCase):

    parent_issue = {
        'key': "TEST-1",
        'fields': {
            'status': {
                'name': "Not Backlog"
            }
        }
    }

    def test_gets_parent_of_subtask(
        self, mock_get_issue, mock_set_backlog_parent_issue_status,
        mock_set_backlog_parent_issue_assignee, mock_set_backlog_issue_estimate
    ):
        mock_get_issue.return_value = self.parent_issue
        get_backlog_parent_issue({
            'fields': {
                "parent": {
                    'key': "TEST-1"
                }
            }
        })
        mock_get_issue.assert_called_once_with("TEST-1")
        mock_set_backlog_parent_issue_status.assert_called_once_with(
            self.parent_issue
        )
        mock_set_backlog_parent_issue_assignee.assert_called_once_with(
            self.parent_issue
        )
        mock_set_backlog_issue_estimate.assert_called_once_with("TEST-1")

    def test_gets_self_if_not_subtask(
        self, mock_get_issue, mock_set_backlog_parent_issue_status,
        mock_set_backlog_parent_issue_assignee, mock_set_backlog_issue_estimate
    ):
        get_backlog_parent_issue(self.parent_issue)
        mock_get_issue.assert_not_called()
        mock_set_backlog_parent_issue_status.assert_called_once_with(
            self.parent_issue
        )
        mock_set_backlog_parent_issue_assignee.assert_called_once_with(
            self.parent_issue
        )
        mock_set_backlog_issue_estimate.assert_called_once_with("TEST-1")


@patch('jira.jira.transition_issue')
class SetBacklogParentIssueStatus(unittest.TestCase):

    issue = {
        'key': 'TEST-1',
        'fields': {
            'status': {}
        }
    }

    def test_backlogs_non_backlogged_issues(self, mock_transition_issue):
        self.issue['fields']['status']['name'] = 'Not Backlog'
        set_backlog_parent_issue_status(self.issue)
        mock_transition_issue.assert_called_once_with('TEST-1', "Backlog")

    def test_ignores_issues_already_backlogged(self, mock_transition_issue):
        self.issue['fields']['status']['name'] = 'Backlog'
        set_backlog_parent_issue_status(self.issue)
        mock_transition_issue.assert_not_called()


@patch('jira.jira.assign_issue')
class SetBacklogParentIssueAssignee(unittest.TestCase):

    issue = {
        'key': 'TEST-1',
        'fields': {}
    }

    def test_clears_assignee_when_it_exists(self, mock_assign_issue):
        self.issue['fields']['assignee'] = 'Not None'
        set_backlog_parent_issue_assignee(self.issue)
        mock_assign_issue.assert_called_once_with('TEST-1', None)

    def test_set_backlog_parent_issue_assignee_ignores_assignee_when_none(
        self, mock_assign_issue
    ):
        self.issue['fields']['assignee'] = None
        set_backlog_parent_issue_assignee(self.issue)
        mock_assign_issue.assert_not_called()


class SetBacklogParentIssueEstimate(unittest.TestCase):

    @patch('jira.jira.update_estimate')
    @patch('jira.jira.get_estimate')
    def test_set_backlog_parent_issue_estimate_clears_estimate_when_it_exists(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.return_value = 5
        set_backlog_parent_issue_estimate('TEST-1')
        mock_get_estimate.assert_called_once_with("TEST-1")
        mock_update_estimate.assert_called_once_with('TEST-1', None)

    @patch('jira.jira.update_estimate')
    @patch('jira.jira.get_estimate')
    def test_set_backlog_issue_estimate_does_not_update_when_estimate_is_none(
        self, mock_get_estimate, mock_update_estimate
    ):
        mock_get_estimate.return_value = None
        set_backlog_parent_issue_estimate('TEST-1')
        mock_get_estimate.assert_called_once_with("TEST-1")
        mock_update_estimate.assert_not_called()
