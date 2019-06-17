import unittest
from unittest.mock import patch
from jira import jira
from jira.issues import issue_event


class IssuesTest(unittest.TestCase):

    @patch('jira.jira.get_issue')
    def test_only_correct_project_gets_acted_on(self, mock_get_issue):
        issue_event({
            "issue": {
                "fields": {
                    "project": {
                        "key": "NOT-" + jira.PROJ_KEY
                    },
                    "issuetype": {
                        "name": "Story",
                        "subtask": False
                    }
                }
            }
        })
        mock_get_issue.assert_not_called()
