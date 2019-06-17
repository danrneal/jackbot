from functional_tests.base import FunctionalTest
from jira import jira


class EstimateUpdatedTest(FunctionalTest):

    def test_subtask_hours_added_to_parent(self):
        # Abe adds hours to some subtasks in the backlog, the parent issue is
        # unaffected
        parent = jira.get_issue(self.issue_keys[0])
        subtasks = parent['fields']['subtasks']
        jira.update_estimate(subtasks[0]['key'], 8)
        jira.update_estimate(subtasks[1]['key'], 3)
        parent = jira.get_issue(self.issue_keys[2])
        subtasks = parent['fields']['subtasks']
        jira.update_estimate(subtasks[0]['key'], 5)
        jira.update_estimate(subtasks[1]['key'], 2)
        self.assertEqual(jira.get_estimate(self.issue_keys[0]), None)
        self.assertEqual(jira.get_estimate(self.issue_keys[1]), None)
        self.assertEqual(jira.get_estimate(self.issue_keys[2]), None)

        # Abe adds a couple of issues to the sprint, the parent issue
        # estimate updates to reflect the sum of the subtasks
        jira.add_issues_to_sprint(self.sprint_id, self.issue_keys[:2])
        self.assertEqual(jira.get_estimate(self.issue_keys[0]), 11)
        self.assertEqual(jira.get_estimate(self.issue_keys[1]), 0)
        self.assertEqual(jira.get_estimate(self.issue_keys[2]), None)

        # Abe adds hours to some subtasks in the sprint, the parent issue
        # reflects the change
        parent = jira.get_issue(self.issue_keys[1])
        subtasks = parent['fields']['subtasks']
        jira.update_estimate(subtasks[0]['key'], 5)
        jira.update_estimate(subtasks[1]['key'], 3)
        self.assertEqual(jira.get_estimate(self.issue_keys[1]), 8)
        self.assertEqual(jira.get_estimate(self.issue_keys[0]), 11)
        self.assertEqual(jira.get_estimate(self.issue_keys[2]), None)

        # Abe creates a subtask with an estimate, the parent issue updates
        estimate_field = jira.get_estimate_field(self.issue_keys[0])
        jira.create_issue(
            jira.PROJ_KEY, "Story Task", "test0c", self.issue_keys[0],
            **{estimate_field: 2}
        )
        self.assertEqual(jira.get_estimate(self.issue_keys[0]), 13)
        self.assertEqual(jira.get_estimate(self.issue_keys[1]), 8)
        self.assertEqual(jira.get_estimate(self.issue_keys[2]), None)

        # Abe deletes a subtask, the parent issue updates
        parent = jira.get_issue(self.issue_keys[1])
        subtasks = parent['fields']['subtasks']
        jira.delete_issue(subtasks[0]['key'])
        self.assertEqual(jira.get_estimate(self.issue_keys[1]), 3)
        self.assertEqual(jira.get_estimate(self.issue_keys[0]), 13)
        self.assertEqual(jira.get_estimate(self.issue_keys[2]), None)

        # Abe removes an issue from the sprint, the parent's issue resets its
        # estimate to None
        jira.remove_issues_from_sprint([self.issue_keys[0]])
        self.assertEqual(jira.get_estimate(self.issue_keys[0]), None)
        self.assertEqual(jira.get_estimate(self.issue_keys[1]), 3)
        self.assertEqual(jira.get_estimate(self.issue_keys[2]), None)
