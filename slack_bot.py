import os
import json
from typing import *
import asyncio

from slack_bolt.app.async_app import AsyncApp
from slack_sdk import WebClient
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from config import CONFIG

RELEVANT_CHANNEL_ID = CONFIG["SLACK_RELEVANT_CHANNEL_ID"]
TUTOR_ID = CONFIG["SLACK_TUTOR_ID"]

# All the async code was kinda taken from this Github issue.
# https://github.com/slackapi/bolt-python/issues/592#issuecomment-1042368085
async def run_app(
        pipe, 
        bot_token: str,
        signing_secret: str,
        socket_token: str
    ):

    # global client
    client = WebClient(token=bot_token)

    app = AsyncApp(
        token=bot_token,
        signing_secret=signing_secret
    )

    @app.event("message")
    async def receive_messages(message, context):
        # If not from the tutor then don't relay to Discord.
        if not context.user_id == TUTOR_ID:
            return
        
        # Possibly make it able to deal with attachments.
        pipe.send(message["text"])

    handler = AsyncSocketModeHandler(
                app, socket_token
            )
    
    asyncio.create_task(poll_msg(pipe, client))

    await handler.start_async()

# The background task.
# Poll for messages and relay to Slack basically.
async def poll_msg(pipe: "Pipe", client: WebClient):
    while True:
        await asyncio.sleep(2)
        if not pipe.poll():
            continue
        
        # Relevant Slack API docs
        # https://slack.dev/python-slack-sdk/web/index.html#messaging
        client.chat_postMessage(
            channel=RELEVANT_CHANNEL_ID,
            text=pipe.recv()
        )