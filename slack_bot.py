import os
import json
from typing import *
import asyncio

from slack_bolt.app.async_app import AsyncApp
from slack_sdk import WebClient
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from config import CONFIG

CHANNEL_MAP = CONFIG["CHANNEL_MAP"]
TUTOR_ID = CONFIG["SLACK_TUTOR_ID"]
SLACK_BOT_ID = CONFIG["SLACK_BOT_ID"]
SLACK_USERID_NAME_MAP = CONFIG["SLACK_USERID_NAME_MAP"]

# All the async code was kinda taken from this Github issue.
# https://github.com/slackapi/bolt-python/issues/592#issuecomment-1042368085
async def run_app(
        pipe, 
        bot_tokens: Dict[str, str],
        signing_secret: str,
        socket_token: str
    ):
    # client = WebClient(token=bot_token)

    CLIENTS = {
        bot_name: WebClient(token=bot_tokens[bot_name]) for bot_name in bot_tokens
    }

    app = AsyncApp(
        token=bot_tokens["T"],
        signing_secret=signing_secret
    )

    @app.event("message")
    async def receive_messages(message, context):
        # If not from the tutor then don't relay to Discord.
        if context.user_id in SLACK_BOT_ID:
            return
        
        # Possibly make it able to deal with attachments.
        sender = SLACK_USERID_NAME_MAP[context.user_id]
        content = f"{sender}: {message['text']}"
        pipe.send(
            {
                "content": content[:1999],
                "channel": context.channel_id
            }
        )

    handler = AsyncSocketModeHandler(
                app, socket_token
        )
    
    asyncio.create_task(poll_msg(pipe, CLIENTS))

    await handler.start_async()

# The background task.
# Poll for messages and relay to Slack basically.
async def poll_msg(pipe: "Pipe", clients: WebClient):
    while True:
        await asyncio.sleep(2)
        if not pipe.poll():
            continue
        
        # Relevant Slack API docs
        # https://slack.dev/python-slack-sdk/web/index.html#messaging
        message = pipe.recv() 
        sender = message["sender"]
        channel = message["channel"]
        clients[sender].chat_postMessage(
            channel=CHANNEL_MAP[f"{channel}_discord"],
            text=message["content"]
        )