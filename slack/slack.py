import json
import os
import requests
import time

API_TOKEN = os.environ['SLACK_API_TOKEN']
WEBHOOK_URL = os.environ.get('SLACK_LIVE_WEBHOOK_URL')

if not WEBHOOK_URL:
    WEBHOOK_URL = os.environ.get('SLACK_TEST_WEBHOOK_URL')

headers = {"Content-Type": "application/json"}


def get_messages(channel_id):
    # get 10 newest messages from channel
    url = f"https://slack.com/api/conversations.history"
    url += f"?token={API_TOKEN}"
    url += f"&channel={channel_id}"
    url += "&limit=10"
    response = requests.request("GET", url)
    if not response.ok:
        print(response.text)
        response.raise_for_status()
    messages = json.loads(response.text)['messages']
    return messages


def delete_message(channel_id, message_ts):
    url = 'https://slack.com/api/chat.delete'
    url += f"?token={API_TOKEN}"
    url += f"&channel={channel_id}"
    url += f"&ts={message_ts}"
    response = requests.request("POST", url)
    if not response.ok:
        print(response.text)
        response.raise_for_status()


def get_latest_bot_message(channel_id, webhook_url):
    message_ts = None
    start = time.time()
    try:
        while time.time() - start < 20:
            messages = get_messages(channel_id)
            bot_id = webhook_url.split('/')[-2]
            for message in messages:
                if message.get('bot_id') == bot_id:
                    message_ts = message['ts']
                    return message
            time.sleep(0.5)
    finally:
        if message_ts:
            delete_message(channel_id, message_ts)


def clear_old_bot_messages(channel_id, webhook_url):
    message_ts = []
    messages = get_messages(channel_id)
    bot_id = webhook_url.split('/')[-2]
    for message in messages:
        if message.get('bot_id') == bot_id:
            message_ts.append(message['ts'])
    for ts in message_ts:
        delete_message(channel_id, ts)


def send_message(message):
    data = json.dumps(message)
    requests.request("POST", WEBHOOK_URL, data=data, headers=headers)
