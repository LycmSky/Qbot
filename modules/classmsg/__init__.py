from functools import reduce
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, ElementMatch, RegexResult, ArgumentMatch, UnionMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from filter import Filter
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.commander import Arg
from graia.ariadne.message.commander.saya import CommandSchema
from graia.ariadne.message.element import Image
from graia.broadcast.exceptions import ExecutionStop
from graia.saya import Channel
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema
from public.ariadne import Bot
from public.database import Database
from modules.mblogSubscribe.mblog import Info, Control

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("微博监控")
channel.description("获取微博动态")
channel.author("Lycm")

class_list = [719037962, 290433302]
msg = '''淘宝拉拉队5000喵币福利免费领，不占助力次数，6次满了也可以点，不互，不互，不是互助哈。看清楚再点谢谢！！！

49哈就说人个有那在着过然自！ https://m.tb.cn/h.fug7g4n  8点-21点可點,分5亿618喵运会红包

拉拉队帮点一下 不需要助力次数'''

# 定时任务
@channel.use(
    SchedulerSchema(timers.crontabify("* * * * * 30")))
async def scheduled_func(app: Ariadne):
    for i in class_list:
        await app.sendGroupMessage(i, MessageChain.create(msg))