from unittest import TestCase
from jira import jira

class FunctionalTest(TestCase):

    def setUp(self):
        sprint = jira.create_sprint("TEST_Sprint", jira.BOARD_ID)
        self.sprint_id = sprint['id']
        self.issue_keys = []
        for i in range(3):
            issue = jira.create_issue(jira.PROJ_KEY, "Story", f"Test_{i}")
            self.issue_keys.append(issue['key'])
            jira.create_issue(
                jira.PROJ_KEY, "Story Task", f"test_{i}a", issue['key']
            )
            jira.create_issue(
                jira.PROJ_KEY, "Story Task", f"test_{i}b", issue['key']
            )

    def tearDown(self):
        for issue_key in self.issue_keys:
            jira.delete_issue(issue_key, delete_subtasks=True)
        jira.delete_sprint(self.sprint_id)