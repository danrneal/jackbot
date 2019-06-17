import requests
import subprocess
import threading
import unittest
from jira import jira
from jira.app import app


class FunctionalTest(unittest.TestCase):

    def setUp(self):
        threading.Thread(target=app.run).start()
        self.serveo = subprocess.Popen(
            ['ssh', '-R', 'jackbot:80:localhost:5000', 'serveo.net'],
            stdin=subprocess.DEVNULL
        )
        # sprint = jira.create_sprint("TEST Sprint", jira.BOARD_ID)
        # self.sprint_id = sprint['id']
        # self.issue_keys = []
        # for i in range(3):
        #     issue = jira.create_issue(jira.PROJ_KEY, "Story", f"test_{i}")
        #     self.issue_keys.append(issue['key'])
        #     jira.create_issue(
        #         jira.PROJ_KEY, "Story Task", f"test_{i}a", issue['key']
        #     )
        #     jira.create_issue(
        #         jira.PROJ_KEY, "Story Task", f"test_{i}b", issue['key']
        #     )

    def tearDown(self):
        self.serveo.kill()
        requests.request("POST", 'http://127.0.0.1:5000/shutdown')
        # for issue_key in self.issue_keys:
        #     jira.delete_issue(issue_key, delete_subtasks=True)
        # jira.delete_sprint(self.sprint_id)
