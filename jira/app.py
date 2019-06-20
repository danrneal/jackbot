import flask
import json
import threading
from jira.issues import issue_event, q

app = flask.Flask(__name__)
threading.Thread(target=issue_event).start()


@app.route('/', methods=['POST', 'GET'])
def webhook():
    if flask.request.method == 'POST':
        data = json.loads(flask.request.data.decode())
        if str(data.get("webhookEvent")).startswith("jira:issue_"):
            q.put(data)
        return 'OK'
    return 'JackBot is running!'


def shutdown_server():
    q.put('shutdown')
    func = flask.request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return
    func()


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'
