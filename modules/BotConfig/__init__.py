import json, re
import database
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.parser.base import MatchContent
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Member
from graia.broadcast.interrupt import InterruptControl
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from distutils.log import info
from aip import AipImageClassify
from graia.broadcast.builtin.decorators import Depend
from graia.broadcast.exceptions import ExecutionStop

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("控制台")
channel.description("对机器人进行相关设置")
channel.author("Lycm")

db = database.databaseInit('users')

def check_user():
    async def check_user_deco(app: Ariadne, friend: Friend):
        if friend.id not in db.find({},{ "_id": 0, "whitelist": 1 })[0]['whitelist']:
            await app.sendFriendMessage(friend, MessageChain.create("权限不足"))
            raise ExecutionStop
    return Depend(check_user_deco)

# 创建消息处理器，接好友消息中的 .config 命令
@channel.use(ListenerSchema(
    listening_events=[FriendMessage], 
    decorators=[
        MatchContent(".config"),
        check_user()]
))
async def imageClassify(app: Ariadne, friend: Friend, message: MessageChain):
    await app.sendFriendMessage(friend, MessageChain.create('配置'))
