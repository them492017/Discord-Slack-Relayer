# TODO LIST (no particular order)
# Dealing with attachment.
# Dealing with all types of mentions.
# Dealing with edit/delete and syncing with Slack.
# Dealing with reply and thread.
import requests
import json
from typing import *

import discord
from discord.ext import tasks

from config import CONFIG

# Task that will be executed periodically.
# Docs: https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
# Poll for messages then relay to Discord.
@tasks.loop(seconds=2.0)
async def poll_msg(pipe: 'Pipe', discord_client: 'MyClient'):
    if not pipe.poll():
        return
    
    await discord_client.relay_msg(pipe.recv())

# Docs for Discord py: https://discordpy.readthedocs.io/en/stable/
class MyClient(discord.Client):
    # This is for mention mapping.
    # Map from Discord's username to Slack's id
    USER_MAP: Dict[str, str] = CONFIG["DISCORD_SLACK_USER_MAP"]
    # The channel the messages are to be relayed from Slack to Discord.
    # If we want to have multiple channels then we can define a mapping 
    # between channels.
    RELEVANT_CHANNEL_ID = CONFIG["DISCORD_RELEVANT_CHANNEL_ID"]
    
    def __init__(self, pipe,  **kwargs):
        super().__init__(**kwargs)
        # Relevant channel to relay messages from Slack
        # Prob general idk
        self.relevant_channel = None
        self.pipe = pipe

    # This is for cosmetics.
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    # Function that runs whenever a message is sent.
    async def on_message(self, message: discord.Message):

        if (message.author == self.user):
            return

        new_msg = self.mention_replace(message)
        self.pipe.send(new_msg)

    async def relay_msg(self, msg: str):
        if self.relevant_channel is None:
            self.relevant_channel = await self.fetch_channel(self.RELEVANT_CHANNEL_ID)

        await self.relevant_channel.send(
            content=msg
        )

    # The docs use this method to initiate the task.
    # Gonna do the same.
    async def setup_hook(self) -> None:
        poll_msg.start(self.pipe, self)

    # This function is not the most efficient thing in the world.
    # Feel free to optimise idk.
    def mention_replace(self, msg: discord.Message) -> str:
        mentions = msg.mentions
        msg_str = msg.content

        for user in mentions:
            msg_str = msg_str.replace(
                f"<@{user.id}>", f"<@{self.USER_MAP[user.name]}>"
            )

        return msg_str



def init_bot(pipe) -> MyClient:
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(pipe, intents=intents)

    return client