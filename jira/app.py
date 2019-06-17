import flask
import json
from jira.issues import issue_event

app = flask.Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def webhook():
    if flask.request.method == 'POST':
        data = json.loads(flask.request.data.decode())
        if str(data.get("webhookEvent")).startswith("jira:issue_"):
            issue_event(data)
        return 'OK'
    return 'JackBot is running!'


def shutdown_server():
    func = flask.request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'
