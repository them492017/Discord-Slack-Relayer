# TODO LIST (no particular order)
# Dealing with attachment.
# Dealing with all types of mentions.
# Dealing with edit/delete and syncing with Slack.
# Dealing with reply and thread.
from typing import Any, TYPE_CHECKING

import discord
from discord.ext import tasks

import config

if TYPE_CHECKING:
    from multiprocessing.connection import Connection


# Task that will be executed periodically.
# Docs: https://discordpy.readthedocs.io/en/latest/ext/tasks/index.html
# Poll for messages then relay to Discord.
@tasks.loop(seconds=2.0)
async def poll_msg(pipe: 'Connection', discord_client: 'MyClient') -> None:
    if not pipe.poll():
        return
    msg = pipe.recv()
    await discord_client.relay_msg(msg["content"], msg["channel"])


# Docs for Discord py: https://discordpy.readthedocs.io/en/stable/
class MyClient(discord.Client):
    # This is for mention mapping.
    # Map from Discord's username to Slack's id
    USER_MAP: dict[str, str] = config.DISCORD_SLACK_USER_MAP
    # Map from Discord's username to initial.
    # Used to point to the correct bot.
    NAME_INITIAL_MAP: dict[str, str] = config.DISCORD_NAME_INITIAL_MAP
    # # The channel the messages are to be relayed from Slack to Discord.
    # # If we want to have multiple channels then we can define a mapping
    # # between channels.
    # RELEVANT_CHANNEL_ID = config.DISCORD_RELEVANT_CHANNEL_ID
    SLACK_CHANNEL_MAP: dict[str, int] = config.SLACK_CHANNEL_MAP

    def __init__(self, pipe: 'Connection', **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Relevant channel to relay messages from Slack
        # Prob general idk
        self.relevant_channels: dict[str, discord.TextChannel] = {}
        self.pipe = pipe

    # This is for cosmetics.
    async def on_ready(self) -> None:
        print(f'Logged on as {self.user}!')

    # Function that runs whenever a message is sent.
    async def on_message(self, message: discord.Message) -> None:
        if (message.author == self.user):
            return

        # print(message.attachments)
        new_msg = self.mention_replace(message)
        sender = self.NAME_INITIAL_MAP[message.author.name]
        channel_id = message.channel.id
        self.pipe.send(
            {
                "content": new_msg,
                "sender": sender,
                "channel": channel_id
            }
        )

    async def relay_msg(self, msg: str, channel_id: str) -> None:
        if channel_id not in self.SLACK_CHANNEL_MAP:
            return

        mapped_id = self.SLACK_CHANNEL_MAP[channel_id]

        if channel_id not in self.relevant_channels:
            channel = await self.fetch_channel(mapped_id)
            if isinstance(channel, discord.TextChannel):  # this should always hold
                self.relevant_channels[channel_id] = channel
            else:
                return

        await self.relevant_channels[channel_id].send(
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
            if user.name not in self.USER_MAP:
                continue
            msg_str = msg_str.replace(
                f"<@{user.id}>", f"<@{self.USER_MAP[user.name]}>"
            )

        return msg_str


def init_bot(pipe: 'Connection') -> MyClient:
    intents = discord.Intents.default()
    intents.message_content = True
    client = MyClient(pipe, intents=intents)

    return client
