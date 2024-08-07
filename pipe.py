from typing import Optional, TypedDict
from multiprocessing.connection import Connection


class RelayedDiscordMessage(TypedDict):
    content: str
    sender_id: int
    channel_id: int


class RelayedSlackMessage(TypedDict):
    content: str
    sender_id: str
    channel_id: str


def send_discord_msg(pipe: Connection, msg_details: RelayedDiscordMessage) -> None:
    pipe.send(msg_details)


def recv_discord_msg(pipe: Connection) -> Optional[RelayedDiscordMessage]:
    if pipe.poll():
        return pipe.recv()

    return None


def send_slack_msg(pipe: Connection, msg_details: RelayedSlackMessage) -> None:
    pipe.send(msg_details)


def recv_slack_msg(pipe: Connection) -> Optional[RelayedSlackMessage]:
    if pipe.poll():
        return pipe.recv()

    return None
