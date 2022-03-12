from datetime import datetime
import database
import re
from filter import Filter
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
from graia.ariadne.message.commander.saya import  CommandSchema
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.commander import Commander, Slot, Arg

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
        "blackList": {
            "Friends": [],
            "Groups": []
        },
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

@channel.use(
        CommandSchema(
        "[.微博 | .mblog]",
        {"open": Arg("[--on|-O|-开启]", bool, False), 
        "close": Arg("[--off|-C|-关闭]", bool, False),
        "nodisturb": Arg("[--nodis|-T|-勿扰] {}", str, ""),
        "add": Arg("[--add|-A|-订阅] {}", str, ""),
        "delete": Arg("[--del|-D|-取消订阅] {}", str, "")}))
async def control(open, close, nodisturb, add, delete, app: Ariadne, event:MessageEvent, message: MessageChain):
    blackList = mods.find_one({"name": "mblogSubscribe"})['blackList']
    subscribe = mods.find_one({"name": "mblogSubscribe"})['subscribe']
    filter = Filter(mod_name="mblogSubscribe", event=event).main
    # 处理群组消息
    if event.type=="GroupMessage":
        groupId = event.sender.group.id
        if open and filter(9): # 开启
            if blackList['Groups'].count(groupId):
                blackList['Groups'].remove(groupId)
                await app.sendGroupMessage(groupId, MessageChain.create('已开启微博订阅功能'))

        if close and filter(13): # 关闭
            if not blackList['Groups'].count(groupId):
                blackList['Groups'].append(groupId)
                print (blackList['Groups'])
                await app.sendGroupMessage(groupId, MessageChain.create('已关闭微博订阅功能'))

        if add !="" and filter(13): # 订阅
            userIds = re.findall(r'(\d+)', add)
            for userId in userIds:
                subscribe[userId] = subscribe[userId] if userId in subscribe else {}
                subscribe[userId][str(groupId)] = "group"
            await app.sendGroupMessage(groupId, MessageChain.create(f'已订阅{userIds}！'))

        if delete !="" and filter(13): # 取消订阅
            userIds = re.findall(r'(\d+)', delete)
            for userId in userIds:
                print (userId)
                if userId in subscribe:
                    if str(groupId) in subscribe[userId]:
                        subscribe[userId].pop(str(groupId))
                    if subscribe[userId]=={}:
                        subscribe.pop(userId)
            await app.sendGroupMessage(groupId, MessageChain.create(f'已取消订阅{userIds}！'))

    # 处理好友消息
    if event.type=="FriendMessage":
        senderId = event.sender.id
        if open and filter(8): # 开启
            if blackList['Friends'].count(senderId):
                blackList['Friends'].remove(senderId)
                await app.sendFriendMessage(senderId, MessageChain.create('已开启微博订阅功能'))

        if close and filter(12): # 关闭
            if not blackList['Friends'].count(senderId):
                blackList['Friends'].append(senderId)
                print (blackList['Friends'])
                await app.sendFriendMessage(senderId, MessageChain.create('已关闭微博订阅功能'))

        if add !="" and filter(12): # 订阅
            userIds = re.findall(r'(\d+)', add)
            for userId in userIds:
                subscribe[userId] = subscribe[userId] if userId in subscribe else {}
                subscribe[userId][str(senderId)] = "friend"
            await app.sendFriendMessage(senderId, MessageChain.create(f'已订阅{userIds}！'))

        if delete !="" and filter(12): # 取消订阅
            userIds = re.findall(r'(\d+)', delete)
            for userId in userIds:
                if userId in subscribe:
                    if str(senderId) in subscribe[userId]:
                        subscribe[userId].pop(str(senderId))
                    if subscribe[userId]=={}:
                        subscribe.pop(userId)
            await app.sendFriendMessage(senderId, MessageChain.create(f'已取消订阅{userIds}！'))

    mods.update_one({"name": "mblogSubscribe"}, {"$set": {"blackList": blackList}})
    mods.update_one({"name": "mblogSubscribe"}, {"$set": {"subscribe": subscribe}})
    