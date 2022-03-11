from datetime import datetime
import database
import re
from functools import reduce
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.scheduler.saya import GraiaSchedulerBehaviour, SchedulerSchema
from graia.ariadne.model import Group, Member, Friend
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.parser.base import MatchContent
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.scheduler import GraiaScheduler
from graia.scheduler import timers
from graia.ariadne.model import MiraiSession

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("微博监控")
channel.description("获取微博动态")
channel.author("Lycm")

# 初始化数据库
mods = database.databaseInit('mods')
if mods.find_one({"name": "mblogSubscribe"}) == None:
    mods.insert_one({
        "name": "mblogSubscribe",
        "enabled": True,
        "blackList": [],
        "whiteList": [],
        "subscribe": {},
        "data": {}
        })

# 文本格式化
header = '''{}
{}（{}）发布了新微博：
    {}'''
footer = '''
原帖链接：{}'''

@channel.use(
    SchedulerSchema(timer=timers.every_minute()))
async def scheduled_func(app: Ariadne):
    for uid,  subscribers in mods.find_one({"name": "mblogSubscribe"})['subscribe'].items():
        mblogList = (f"https://m.weibo.cn/api/container/getIndex?&containerid=107603{uid}")
        session = get_running(Adapter).session
        async with session.get(mblogList) as r:
            imgBase = await r.json()
            mblog = imgBase['data']['cards'][0]['mblog']
            text = re.sub(r'<[^>]+>', '', mblog['text'])
            screen_name = mblog['user']['screen_name']
            scheme = imgBase['data']['cards'][0]['scheme']
            created_at = mblog['created_at']
            id = mblog['id']

        try:
            mods.find_one({"name": "mblogSubscribe"})['data'][id]
        except:
            for subscriber, t in subscribers.items():
                send = app.sendGroupMessage if t=="group" else app.sendFriendMessage
                response_header = header.format(datetime.strptime(created_at, '%a %b %d %H:%M:%S +0800 %Y'), screen_name, uid, text)
                response_footer = footer.format(scheme)
                if mblog['pic_num']:
                    MessageChain_pic = map(lambda x: MessageChain.create(Image(url=x['url'])), mblog['pics'])
                    response = reduce(lambda x, y: x+y, MessageChain_pic, MessageChain.create(response_header))+response_footer
                    await send(subscriber, response)
                else:
                    await send(subscriber, MessageChain.create(response_header+response_footer))

                data = mods.find_one({"name": "mblogSubscribe"})['data']
                data[id] = {"uid": uid,
                    "screen_name": screen_name,
                    "created_at": created_at,
                    "text": text,
                    "scheme": scheme}
                mods.update_one({"name": "mblogSubscribe"}, {"$set": {"data": data}})