from modules.Weather.data import Command
from tools import timefomart
from functools import reduce
from graia.saya import Channel
from graia.scheduler.saya import SchedulerSchema
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.scheduler import timers
from graia.ariadne.message.commander.saya import  CommandSchema
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.message.commander import Arg
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.app import Ariadne
from graia.ariadne.model import MiraiSession
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, ElementMatch, RegexResult, ArgumentMatch, UnionMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from modules.Bilibili.get_info import API
from graia.ariadne.message.element import Xml, App
import ast
# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("天气预报")
channel.description("定时发送天气情况")
channel.author("Lycm")


# 定时任务
@channel.use(
    SchedulerSchema(timer=timers.every_minute()))
async def scheduled_func(app: Ariadne):
    pass

# 小程序卡片解析
@channel.use(
    ListenerSchema(
        listening_events = [GroupMessage, FriendMessage], 
        inline_dispatchers = [Twilight([ElementMatch(App)])]))
async def twilight_handler(app: Ariadne, msg: MessageChain):
    content = ast.literal_eval(msg.dict()['__root__'][1]['content'])
    if content['meta']['detail_1']['title'] == "哔哩哔哩":
        url = content['meta']['detail_1']['qqdocurl'].replace("\\", "")
        x = API()
        bvid = await x.get_bvid(url)
        await app.sendFriendMessage(2417003944, MessageChain.create(await x.get_videoinfo(bvid)))


twilight = Twilight([
                FullMatch(".B").help("匹配 .B"), 
                # "open" @ ArgumentMatch("--open", "-O", "-开启", action="store_true", default=False, optional=True).help("开启功能"),
                # "close" @ ArgumentMatch("--close", "-C", "-关闭", action="store_false", default=True, optional=True).help("关闭功能"),
                # "help" @ ArgumentMatch("--help", "-h", "-?", "-？", "-帮助", action="store_true").help("显示该帮助"),
                "inquiry" @ ArgumentMatch("--inquiry", "-F", "-查询", optional=True).help("查询信息"),
            ])

@channel.use(
    ListenerSchema(
        listening_events = [GroupMessage, FriendMessage], 
        inline_dispatchers = [twilight]))
async def twilight_handler(app: Ariadne, event: MessageEvent, inquiry: RegexResult):
    x = API()
    print (inquiry.result.asDisplay())
    await app.sendFriendMessage(2417003944, MessageChain.create(await x.get_userinfo(inquiry.result.asDisplay())))