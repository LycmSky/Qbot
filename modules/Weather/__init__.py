import cmd
from datetime import datetime

from modules.Weather.data import Command
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
from modules.Weather.weatherAPI import API
from graia.ariadne.message.parser.base import DetectPrefix
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.app import Ariadne
from graia.ariadne.model import MiraiSession
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, ParamMatch, RegexResult, ArgumentMatch, UnionMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema


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


twilight = Twilight([
                FullMatch(".天气").help("匹配 .天气"), 
                "open" @ ArgumentMatch("--open", "-O", "-开启", action="store_true", default=False, optional=True).help("开启功能"),
                "close" @ ArgumentMatch("--close", "-C", "-关闭", action="store_false", default=True,optional=True).help("关闭功能"),
                "help" @ ArgumentMatch("--help", "-h", "-?", "-？", "-帮助", action="store_true").help("显示该帮助"),
                "city" @ ArgumentMatch("--city", "-c", "-城市").help("设置目标城市"),
            ])

@channel.use(
    ListenerSchema(
        listening_events = [GroupMessage, FriendMessage], 
        inline_dispatchers = [twilight]))
async def twilight_handler(
    event: MessageEvent, 
    app: Ariadne, 
    open: RegexResult, 
    close: RegexResult,
    help: RegexResult,
    city: RegexResult
):
    # 实例化
    t = Command(app, event)
    api = API('SK0rkwg64J1b3JuGG')
    # 帮助
    await t.help(twilight) if help.result else None
    # 开关
    await t.switch(open.result and close.result) if open.result==close.result else None
    # 查询天气
    location = city.result.asDisplay() if city.matched else t.user_data["location"]
    await t.sendMessage(MessageChain.create(await api.hourly(location)))
    

    
    # await app.sendMessage(event, "收到指令: " + param.result)


# # 辅助功能
# @channel.use(
#         CommandSchema(
#         command = ".",
#         settings = {
#             "help": Arg("[--help|-h|?|？|-帮助]", bool, False),
#             "test": Arg("[--test]", bool, False),
#             "city": Arg("[--city|-c|-城市]{}", str, ""),
#             "hours": Arg("[--hours|-H|-时间]{}", str, "")
#         },
#         # decorators=[DetectPrefix('1')]
#         ))
# async def control(help, test, city, hours, app: Ariadne, event:MessageEvent, message: MessageChain):
#     print (message)
#     x = HELP(app, event)
#     h = await x.eee(help, test=test, city=city, hours=hours)
#     await x.aaa("Weather", h) if h!=None else "a"
#     # imginfo = await inc.wait(waiter)
#     # api = API('SK0rkwg64J1b3JuGG')
#     # # a = await api.hourly(city, hours=hours)
#     # a, _ = await api.alarm(city, [])
#     # await app.sendFriendMessage(event.sender.id, MessageChain.create(a))