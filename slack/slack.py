import json
import os
import requests
import time

API_TOKEN = os.environ['SLACK_API_TOKEN']


def get_message(channel_id, webhook_url):

    message_ts = None
    start = time.time()
    try:
        while time.time() - start < 60:

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
            bot_id = webhook_url.split('/')[-2]
            for message in messages:
                if message.get('bot_id') == bot_id:
                    message_ts = message['ts']
                    return message

            time.sleep(5)

    finally:
        if message_ts:
            url = 'https://slack.com/api/chat.delete'
            url += f"?token={API_TOKEN}"
            url += f"&channel={channel_id}"
            url += f"&ts={message_ts}"
            response = requests.request("POST", url)
            if not response.ok:
                print(response.text)
                response.raise_for_status()
