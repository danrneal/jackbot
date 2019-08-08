import flask
import json
import queue
import threading
from jira.issues import issue_event
from jira.sprints import sprint_event, scheduler

app = flask.Flask(__name__)
q = queue.Queue()


def handle_webhook_from_q():
    while True:
        data = q.get()
        if data == 'shutdown':
            break
        issue = data.get('issue')
        if issue:
            issue_event(issue)
        sprint = data.get('sprint')
        if sprint:
            sprint_event(sprint)


threading.Thread(target=handle_webhook_from_q, daemon=True).start()
threading.Thread(target=scheduler, daemon=True).start()


@app.route('/', methods=['POST', 'GET'])
def webhook():
    if flask.request.method == 'POST':
        data = json.loads(flask.request.data.decode())
        q.put(data)
        return 'OK'
    return 'JackBot is running!'
