import importlib
import os
import requests
import socket
import subprocess
import time
import threading
import unittest
from jira import jira

STAGING_SERVER = os.environ.get('STAGING_SERVER')
MAX_WAIT = 60

if not STAGING_SERVER:
    import jira.app as app
    SERVEO_SUBDOMAIN = os.environ.get('SERVEO_SUBDOMAIN')


class FunctionalTest(unittest.TestCase):

    def setUp(self):
        self.set_up_server()
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
        issue = self.setup_issue("Story", "test_3")
        self.issue_keys.append(issue['key'])
        issue = self.setup_issue("Task", "test_4")
        self.issue_keys.append(issue['key'])
        self.wait_for(lambda: self.assertEqual(
            requests.request("GET", self.live_server_url).text,
            "JackBot is running!"
        ))

    def tearDown(self):
        for issue_key in self.issue_keys + self.subtask_keys:
            jira.transition_issue(issue_key, "Archive", "Won't Do")
            jira.assign_issue(issue_key, None)
        jira.delete_sprint(self.sprint_id)
        if not STAGING_SERVER:
            self.serveo.kill()
            self.serveo.wait()

    def set_up_server(self):
        if STAGING_SERVER:
            self.live_server_url = 'https://' + STAGING_SERVER
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', 0))
            port = sock.getsockname()[1]
            sock.close()
            subdomain = SERVEO_SUBDOMAIN
            self.live_server_url = f'https://{subdomain}.serveo.net'
            self.serveo = subprocess.Popen(
                ['ssh', '-R', f'{subdomain}:80:localhost:{port}', 'serveo.net'],
                stdin=subprocess.DEVNULL
            )
            importlib.reload(app)
            threading.Thread(
                target=app.app.run,
                daemon=True,
                kwargs={'port': port}
            ).start()

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
