import flask
import json
import queue
import threading
from jira.issues import issue_event
from jira.sprints import sprint_started

app = flask.Flask(__name__)
q = queue.Queue()


def handle_webhook_from_q():
    while True:
        data = q.get()
        if data == 'shutdown':
            break
        if str(data.get("webhookEvent")).startswith("jira:issue_"):
            issue_event(data)
        elif str(data.get("webhookEvent")) == "sprint_started":
            sprint_started(data)


threading.Thread(target=handle_webhook_from_q).start()


def shutdown_server():
    q.put('shutdown')
    func = flask.request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return
    func()


@app.route('/', methods=['POST', 'GET'])
def webhook():
    if flask.request.method == 'POST':
        data = json.loads(flask.request.data.decode())
        q.put(data)
        return 'OK'
    return 'JackBot is running!'


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'
