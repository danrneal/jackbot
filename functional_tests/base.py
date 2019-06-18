import os
import requests
import subprocess
import time
import threading
import unittest
from jira import jira

STAGING_SERVER = os.environ.get('STAGING_SERVER')
MAX_WAIT = 20

if not STAGING_SERVER:
    from jira.app import app


class FunctionalTest(unittest.TestCase):

    def setUp(self):
        if STAGING_SERVER:
            self.live_server_url = 'https://' + STAGING_SERVER
        else:
            self.live_server_url = 'https://jackbot.serveo.net'
            self.serveo = subprocess.Popen(
                ['ssh', '-R', 'jackbot:80:localhost:5000', 'serveo.net'],
                stdin=subprocess.DEVNULL
            )
            threading.Thread(target=app.run).start()
        sprint = jira.create_sprint("TEST Sprint", jira.BOARD_ID)
        self.sprint_id = sprint['id']
        self.issue_keys = []
        for i in range(3):
            issue = jira.create_issue(jira.PROJ_KEY, "Story", f"test_{i}")
            self.issue_keys.append(issue['key'])
            jira.create_issue(
                jira.PROJ_KEY, "Story Task", f"test_{i}a", issue['key']
            )
            jira.create_issue(
                jira.PROJ_KEY, "Story Task", f"test_{i}b", issue['key']
            )
        self.wait_for(lambda: self.assertEqual(
            requests.request("GET", self.live_server_url).text,
            "JackBot is running!"
        ))

    def tearDown(self):
        for issue_key in self.issue_keys:
            jira.delete_issue(issue_key, delete_subtasks=True)
        jira.delete_sprint(self.sprint_id)
        if not STAGING_SERVER:
            requests.request("POST", self.live_server_url + '/shutdown')
            self.serveo.kill()

    @staticmethod
    def wait_for(fn):
        start_time = time.time()
        while True:
            try:
                return fn()
            except AssertionError as e:
                if time.time() - start_time > MAX_WAIT:
                    raise e
                time.sleep(0.5)
