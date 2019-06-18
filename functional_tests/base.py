import os
import requests
import subprocess
import time
import threading
import unittest
from jira import jira
from jira.app import app

MAX_WAIT = 20


class FunctionalTest(unittest.TestCase):

    def setUp(self):
        staging_server = os.environ.get('STAGING_SERVER')
        if staging_server:
            self.live_server_url = 'https://' + staging_server
        else:
            threading.Thread(target=app.run).start()
            self.live_server_url = 'https://jackbot.serveo.net'
            self.serveo = subprocess.Popen(
                ['ssh', '-R', 'jackbot:80:localhost:5000', 'serveo.net'],
                stdin=subprocess.DEVNULL
            )
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
        if self.serveo:
            self.serveo.kill()
            requests.request("POST", self.live_server_url + '/shutdown')


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
