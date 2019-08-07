from functional_tests.base import FunctionalTest
from jira import jira


class StatusUpdatedTest(FunctionalTest):

    def test_parent_status_transitioned_based_on_subtask_status(self):
        # Abe adds an issue to a sprint
        jira.add_issues_to_sprint(self.sprint_id, [self.issue_keys[0]])

        # Abe does a bunch of transitions on the subtasks, the parent issue
        # updates its status automatically
        parent = jira.get_issue(self.issue_keys[0])
        subtasks = parent['fields']['subtasks']
        jira.assign_issue(subtasks[0]['key'])
        jira.assign_issue(subtasks[1]['key'])
        self.wait_for(lambda: self.assertEqual(
            jira.get_issue(self.issue_keys[0])['fields']['status']['name'],
            "Backlog"
        ))

        jira.transition_issue(subtasks[0]['key'], "In Progress")
        self.wait_for(lambda: self.assertEqual(
            jira.get_issue(self.issue_keys[0])['fields']['status']['name'],
            "In Progress"
        ))

        jira.transition_issue(subtasks[0]['key'], "Archive", "Won't Do")
        self.wait_for(lambda: self.assertEqual(
            jira.get_issue(self.issue_keys[0])['fields']['status']['name'],
            "Backlog"
        ))

        jira.transition_issue(subtasks[0]['key'], "Done")
        self.wait_for(lambda: self.assertEqual(
            jira.get_issue(self.issue_keys[0])['fields']['status']['name'],
            "In Progress"
        ))

        jira.transition_issue(subtasks[1]['key'], "Done")
        self.wait_for(lambda: self.assertEqual(
            jira.get_issue(self.issue_keys[0])['fields']['status']['name'],
            "PO Review"
        ))

        jira.transition_issue(subtasks[1]['key'], "In Progress")
        self.wait_for(lambda: self.assertEqual(
            jira.get_issue(self.issue_keys[0])['fields']['status']['name'],
            "In Progress"
        ))

        # Abe backlogs the issue, the issue status goes back to "Backlog"
        jira.remove_issues_from_sprint([self.issue_keys[0]])
        self.wait_for(lambda: self.assertEqual(
            jira.get_issue(self.issue_keys[0])['fields']['status']['name'],
            "Backlog"
        ))
        self.assertEqual(
            jira.get_issue(self.issue_keys[0])['fields']['assignee'], None
        )
