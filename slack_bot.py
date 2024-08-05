from typing import Any, TYPE_CHECKING
import os
import asyncio

from slack_bolt import BoltContext
from slack_bolt.app.async_app import AsyncApp
from slack_sdk import WebClient
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

import config
from pipe import recv_discord_msg, send_slack_msg

if TYPE_CHECKING:
    from multiprocessing.connection import Connection


# All the async code was kinda taken from this Github issue.
# https://github.com/slackapi/bolt-python/issues/592#issuecomment-1042368085
async def run_app(
    pipe: 'Connection',
    bot_tokens: dict[str, str],
    signing_secret: str,
    socket_token: str
) -> None:
    CLIENTS = {
        bot_name: WebClient(token=bot_tokens[bot_name])
        for bot_name in bot_tokens
    }

    app = AsyncApp(
        token=os.environ.get("MAIN_SLACK_TOKEN"),
        signing_secret=signing_secret
    )

    @app.event("message")  # type: ignore
    async def receive_messages(message: dict[str, Any], context: BoltContext) -> None:  # type: ignore
        # If not from the tutor then don't relay to Discord.
        if context.user_id is None or context.user_id in config.SLACK_BOT_ID:
            return

        # Possibly make it able to deal with attachments.
        send_slack_msg(pipe, {
            "content": message['text'],
            "sender_id": context.user_id,
            "channel_id": context.channel_id or "",
        })

    handler = AsyncSocketModeHandler(
        app, socket_token
    )

    asyncio.create_task(poll_msg(pipe, CLIENTS))

    await handler.start_async()


# The background task.
# Poll for messages and relay to Slack basically.
async def poll_msg(pipe: 'Connection', clients: dict[str, WebClient]) -> None:
    while True:
        await asyncio.sleep(2)

        # Relevant Slack API docs
        # https://slack.dev/python-slack-sdk/web/index.html#messaging
        if (msg := recv_discord_msg(pipe)) is not None:
            if len(msg) == 0:
                continue
            # assert len(msg['content']) < MAX_SLACK_MSG_LEN
            clients[msg['sender']].chat_postMessage(  # type: ignore
                channel=config.DISCORD_CHANNEL_MAP[msg['channel_id']],
                text=msg['content']
            )
