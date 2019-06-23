import os
import random
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
            subdomain = ''.join(random.SystemRandom().choices(
                'abcdefghijklmnopqrstuvwxyz0123456789',
                k=random.randint(5, 16)
            ))
            self.live_server_url = f'https://{subdomain}.serveo.net'
            self.serveo = subprocess.Popen(
                ['ssh', '-R', f'{subdomain}:80:localhost:5000', 'serveo.net'],
                stdin=subprocess.DEVNULL
            )
            threading.Thread(target=app.run).start()
        sprint = jira.create_sprint("TEST Sprint", jira.BOARD_ID)
        self.sprint_id = sprint['id']
        self.issue_keys = []
        self.subtask_keys = []
        for i in range(3):
            issue = self.setup_issue("Story", f"test_{i}")
            self.issue_keys.append(issue['key'])
            for c in ['a', 'b']:
                subtask = self.setup_issue(
                    "Story Task", f"test_{i}{c}", issue['key']
                )
                self.subtask_keys.append(subtask['key'])
        self.wait_for(lambda: self.assertEqual(
            requests.request("GET", self.live_server_url).text,
            "JackBot is running!"
        ))

    def tearDown(self):
        for issue_key in self.issue_keys + self.subtask_keys:
            jira.transition_issue(issue_key, "Archive", "Won't Do")
        jira.delete_sprint(self.sprint_id)
        if not STAGING_SERVER:
            requests.request("POST", self.live_server_url + '/shutdown')
            self.serveo.kill()
            self.serveo.wait()

    @staticmethod
    def setup_issue(issuetype, summary, parent_key=None):
        issue = jira.search_for_issue(issuetype, summary, parent_key)
        if issue:
            jira.transition_issue(issue['key'], "Backlog")
            if parent_key:
                jira.update_estimate(issue['key'], 0)
            else:
                jira.update_estimate(issue['key'], None)
        else:
            if parent_key:
                estimate_field = jira.get_estimate_field(parent_key)
                jira.create_issue(
                    issuetype, summary, parent_key, **{estimate_field: 0}
                )
            else:
                issue = jira.create_issue(issuetype, summary, parent_key)
        return issue

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
