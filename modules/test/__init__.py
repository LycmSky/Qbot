import asyncio

from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def friend_message_listener(app: Ariadne, friend: Friend, message: MessageChain):
    await app.sendMessage(friend, MessageChain.create(message.asDisplay()))