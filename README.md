# JackBot

JackBot uses both Jira’s and Slack’s API in order to automate workflows and notify a Scrum team at MobLab Inc. of the burndown rate or potential problems with Jira issues. JackBot serves the following automated functions:

- Updates parent status in Jira when all subtasks of that parent reach a given status
- Adds up all subtask estimates and adds that as the parent estimate
- Rounds fractional estimates up to the nearest integer
- Posts the current burndown rate to a Slack channel every day at a given time or when a new sprint is started regardless of the time
- Lists Jira issues that need to be split or that are missing estimates along with the burndown rate in Slack

## Set-up

Set-up a virtual environment and activate it:

```bash
python3 -m venv env
source env/bin/activate
```

You should see (env) before your command prompt now. (You can type `deactivate` to exit the virtual environment any time.)

Install the requirements:

```bash
pip install -U pip
pip install -r requirements.txt
```

Obtain a Jira API key [here](https://id.atlassian.com/manage-profile/security/api-tokens).

Set up a Jira webhook by following the instructions [here](https://confluence.atlassian.com/adminjiracloud/managing-webhooks-776636231.html). The webhook should trigger on the following events: `issue:created`, `issue:updated`, `issue:deleted`, and `sprint:started`.

Set the global variable `PROJ_KEY` and `BOARD_ID` in `jira/jira.py`.

Obtain a Slack API key [here](https://api.slack.com/apps).

- Configure the webhook in the "Incoming Webhooks" option
- Install your app to the desired workspace
- Copy the "OAuth Access Token" in the "Permissions option (it should start with "xoxb-")

Set the global variable `ALERT_TIME` in `slack/sprints.py`.

Set up your environment variables:

```bash
touch .env
echo FLASK_APP=jira/app.py >> .env
echo JIRA_EMAIL="XXX" >> .env
echo JIRA_API_TOKEN="XXX" >> .env
echo JIRA_SERVER="https://XXX.atlassian.net" >> .env
echo SLACK_API_TOKEN="XXX" >> .env
echo SLACK_LIVE_WEBHOOK_URL="https://hooks.slack.com/services/XXX/XXX/XXX" >> .env
```

Finally you should have port 5000 forwarded to the outside internet (specifically the url of your Jira webhook). This can easily be accomplished with [Serveo](http://serveo.net/):

```bash
ssh -R XXX:80:localhost:5000 serveo.net
```

## Usage

Make sure you are in the virtual environment (you should see (env) before your command prompt). If not `source /env/bin/activate` to enter it.

```bash
Usage: flask run
```

## Screenshots

![Burndown Alert in Slack](https://i.imgur.com/1avbXSl.png)

## Deployment

For provisioning a new server see `deploy_tools/provisioning_notes.md`.

Set the host of your new server as an environment variable:

```bash
export HOST="YOU@HOST.COM"
```

You can deploy automatically to your new server using the following command:

```bash
fab deploy:host=$HOST
```

## Testing Suite

This repository contains a test suite consisting of functional tests and unit tests.

### Functional Tests

These test the program from the outside, from a user's point of view and are also known as Acceptance Tests or End-to-End Tests.

[Serveo](http://serveo.net/) is a great testing tool for exposing a local server to the internet. You can set a subdomain for consistent test results.

Then set your environmental variables. It is recommended that you use DMs between you arn your Slack app for a test webhook and test channel.

```bash
echo SERVEO_SUBDOMAIN="XXX" >> .env
echo SLACK_TEST_WEBHOOK_URL="https://hooks.slack.com/services/XXX/XXX/XXX" >> .env
echo SLACK_TEST_CHANNEL_ID="XXX" >> .env
set -a; source .env; set +a
```

You can run the functional tests with the following command:

```bash
python3 -m unittest discover functional_tests
```

#### _Note: These tests require that the Slack API Token also have the scopes of `im:history` and `chat:write`_

### Unit Tests

These test the program from the inside, from developer's point of view. You can run them with the following commands:

```bash
python3 -m unittest discover jira/tests
python3 -m unittest discover slack/tests
```

## License

JackBot is licensed under the [MIT license](https://github.com/danrneal/jackbot/blob/master/LICENSE).
