import os
from typing import *
from multiprocessing import Process, Pipe
import asyncio
from time import sleep

from discord_bot import init_bot
from slack_bot import run_app


class Runner:
    def __init__(self):
        # These were supposed to be for message queues
        # Apparently these are no longer needed? IDK need more load testing to 
        # determine that.
        self._discord_to_slack_msg = []
        self._slack_to_discord_msg = []

        # Discord bot token
        self._DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

        # Slack bot OAUTH token
        self._SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
        # Slack bot signing secret
        self._SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
        # Slack bot socket token
        self._SLACK_SOCKET_TOKEN = os.environ.get("SLACK_SOCKET_TOKEN")

        # Pipe for IPC between main and the Discord bot.
        self.DISCORD_PIPE, child_discord_pipe = Pipe()
        # I don't think is even needed but just leave it here for now.
        self.DISCORD_BOT = init_bot(child_discord_pipe)

        # Pipe for IPC between main and the Slack bot.
        self.SLACK_PIPE, self.CHILD_SLACK_PIPE = Pipe()

    def start(self):
        # Use multiprocess to create 2 processes, 1 for Slack and 1 for 
        # Discord.
        discord = Process(target=self.run_discord_bot, args=())
        slack = Process(target=self.run_slack_bot, args=())
        discord.start()
        slack.start()

        # Poll messages from Discord then relay to Slack and vice versa.
        # Not sure if message queues should be used, need more load testing.
        
        # Also for now I just send the raw messages over, we prob need more 
        # information than just the raw messages (sender, attachments, etc...)
        while True:
            sleep(1)
            if self.DISCORD_PIPE.poll():
                self.SLACK_PIPE.send(self.DISCORD_PIPE.recv())

            if self.SLACK_PIPE.poll():
                self.DISCORD_PIPE.send(self.SLACK_PIPE.recv())

            
    def run_discord_bot(self):
        self.DISCORD_BOT.run(self._DISCORD_TOKEN)

    def run_slack_bot(self):
        asyncio.run(run_app(
            self.CHILD_SLACK_PIPE,
            self._SLACK_BOT_TOKEN,
            self._SLACK_SIGNING_SECRET,
            self._SLACK_SOCKET_TOKEN
        ))
        
if __name__ == "__main__":
    runner = Runner()
    runner.start()