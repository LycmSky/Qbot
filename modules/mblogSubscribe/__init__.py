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

# 初始化数据库
Database("mblogSubscribe").init_database(
    {
        "name": "mblogSubscribe",
        "enabled": {
            "state": True,
            "Friend": [],
            "Group": []
        },
        "nodisturb": {},
        "whiteList": [],
        "subscribe": {},
        "data": {}
    }
)

def makemsg(okList, errList):
    p, l = "", ""
    for i in okList:
        p += f"    - {i}\n"
    for e in errList:
        l += f"    - {e}\n"
    message = f'''添加订阅：
成功{len(okList)}：
{p[:-1]}
失败{len(errList)}：
{l}'''
    return message

# 定时任务
@channel.use(
    SchedulerSchema(timer=timers.every_minute()))
async def scheduled_func(app: Ariadne):
    database = Database("mblogSubscribe")
    for uid,  subscribers in database.data['subscribe'].items():
        mblog = await Info.get_last_blog(uid)
        for subscriber, type in subscribers.items():
            filter = [  # 条件判断集合
                database.data["enabled"]["state"], # 总开关是否开启
                mblog["id"] not in database.data['data'], # 是否已存在
                database.data["enabled"][type[:-7]].count(int(subscriber))] # 用户是否关闭
            if all(filter):  # 条件判断
                # 构建回复消息
                response = MessageChain.create(
                    f"{mblog['time']}\n"
                    f"{mblog['screen_name']}（{mblog['uid']}）发布了新微博：\n"
                    f"    {mblog['text']}")
                if mblog['pics'] != None:
                    MessageChain_pic = map(lambda x: MessageChain.create(Image(url=x['url'])), mblog['pics'])
                    response = reduce(lambda x, y: x+y, MessageChain_pic, response)
                response += MessageChain.create(f"\n\n原帖链接：{mblog['scheme']}")
                # 发送消息
                send = app.sendGroupMessage if type=="group" else app.sendFriendMessage
                await send(int(subscriber), response)
                # 更新数据库
                database.data['data'][mblog["id"]] = mblog
                database.update("data", database.data['data'])

twilight = Twilight([
                FullMatch(".微博").help("匹配 .微博"), 
                "open" @ ArgumentMatch("--open", "-O", "-开启", action="store_true", default=False, optional=True).help("开启功能"),
                "close" @ ArgumentMatch("--close", "-C", "-关闭", action="store_false", default=True, optional=True).help("关闭功能"),
                "help" @ ArgumentMatch("--help", "-h", "-?", "-？", "-帮助", action="store_true").help("显示该帮助"),
                "uid_list_add" @ ArgumentMatch("-订阅").help("订阅用户,多个id之间用符号隔开"),
                "uid_list_del" @ ArgumentMatch("-取消订阅").help("取消订阅,多个id之间用符号隔开"),
                # "inquiry" @ ArgumentMatch("--inquiry", "-F", "-查询", optional=True).help("查询信息"),
            ])

@channel.use(
    ListenerSchema(
        listening_events = [GroupMessage, FriendMessage], 
        inline_dispatchers = [twilight]))
async def twilight_handler(
    app: Ariadne, event: MessageEvent, help: RegexResult, 
    uid_list_add: RegexResult, uid_list_del: RegexResult,
    open: RegexResult, close: RegexResult):
    print (uid_list_add, uid_list_del)
    database = Database("mblogSubscribe")
    bot = Bot(app, event)
    control = Control(database, bot)
    # 帮助
    await control.help(twilight) if help.result else None
    # 开关
    await control.switch(open.result and close.result) if open.result==close.result else None

# # 辅助功能
# @channel.use(
#         CommandSchema(
#         "[.微博 | .mblog]",
#         {"open": Arg("[--on|-O|-开启]", bool, False), 
#         "close": Arg("[--off|-C|-关闭]", bool, False),
#         "add": Arg("[--add|-A|-订阅] {}", str, ""),
#         "delete": Arg("[--del|-D|-取消订阅] {}", str, ""),
#         "nodisturb": Arg("[--nodis|-T|-勿扰] {}", str, ""),
#         }))
# async def control(open, close, nodisturb, add, delete, app: Ariadne, event:MessageEvent, message: MessageChain):
#     blackList = mods.find_one({"name": "mblogSubscribe"})['blackList']
#     subscribe = mods.find_one({"name": "mblogSubscribe"})['subscribe']
#     filter = Filter(mod_name="mblogSubscribe", event=event).main
#     session = get_running(Adapter).session
#     # 处理群组消息
#     if event.type=="GroupMessage":
#         groupId = event.sender.group.id
#         if open and filter(9): # 开启
#             if blackList['Groups'].count(groupId):
#                 blackList['Groups'].remove(groupId)
#                 await app.sendGroupMessage(groupId, MessageChain.create('已开启微博订阅功能'))

#         if close and filter(13): # 关闭
#             if not blackList['Groups'].count(groupId):
#                 blackList['Groups'].append(groupId)
#                 await app.sendGroupMessage(groupId, MessageChain.create('已关闭微博订阅功能'))

#         if add !="" and filter(13): # 订阅
#             userIds = re.findall(r'(\d+)', add)
#             okList, errList = [], []
#             for userId in userIds:
#                 url = f"https://m.weibo.cn/api/container/getIndex?&containerid=107603{userId}"
#                 async with session.get(url) as r:
#                     imgBase = await r.json()
#                 if imgBase["ok"]:
#                     subscribe[userId] = subscribe[userId] if userId in subscribe else {}
#                     subscribe[userId][str(groupId)] = "group"
#                     okList.append(imgBase["data"]["cards"][0]['mblog']["user"]["screen_name"])
#                 else:
#                     errList.append(userId)
#             await app.sendGroupMessage(groupId, MessageChain.create(makemsg(okList, errList)))

#         if delete !="" and filter(13): # 取消订阅
#             userIds = re.findall(r'(\d+)', delete)
#             for userId in userIds:
#                 if userId in subscribe:
#                     if str(groupId) in subscribe[userId]:
#                         subscribe[userId].pop(str(groupId))
#                     if subscribe[userId]=={}:
#                         subscribe.pop(userId)
#             await app.sendGroupMessage(groupId, MessageChain.create(f'已取消订阅{userIds}！'))

#         if re.search(r'(\d+:\d+)-(\d+:\d+)', nodisturb) != None and filter(13): # 添加勿扰
#             start, stop = re.search(r'(\d+:\d+)-(\d+:\d+)', nodisturb).groups()
#             nodisturbData = mods.find_one({"name": "mblogSubscribe"})['nodisturb']
#             nodisturbData[str(groupId)] = {"type": "group", "start": Time.timefomart(start), "stop": Time.timefomart(stop)}
#             mods.update_one({"name": "mblogSubscribe"}, {"$set": {"nodisturb": nodisturbData}})
#             await app.sendGroupMessage(groupId, MessageChain.create(f'已添加勿扰时段{nodisturb}'))
#     # 处理好友消息
#     if event.type=="FriendMessage":
#         senderId = event.sender.id
#         if open and filter(8): # 开启
#             if blackList['Friends'].count(senderId):
#                 blackList['Friends'].remove(senderId)
#                 await app.sendFriendMessage(senderId, MessageChain.create('已开启微博订阅功能'))

#         if close and filter(12): # 关闭
#             if not blackList['Friends'].count(senderId):
#                 blackList['Friends'].append(senderId)
#                 print (blackList['Friends'])
#                 await app.sendFriendMessage(senderId, MessageChain.create('已关闭微博订阅功能'))

#         if add !="" and filter(12): # 订阅
#             userIds = re.findall(r'(\d+)', add)
#             okList, errList = [], []
#             for userId in userIds:
#                 url = f"https://m.weibo.cn/api/container/getIndex?&containerid=107603{userId}"
#                 async with session.get(url) as r:
#                     imgBase = await r.json()
#                 if imgBase["ok"]:
#                     subscribe[userId] = subscribe[userId] if userId in subscribe else {}
#                     subscribe[userId][str(senderId)] = "friend"
#                     okList.append(imgBase["data"]["cards"][0]['mblog']["user"]["screen_name"])
#                 else:
#                     errList.append(userId)
#             await app.sendFriendMessage(senderId, MessageChain.create(makemsg(okList, errList)))

#         if delete !="" and filter(12): # 取消订阅
#             userIds = re.findall(r'(\d+)', delete)
#             for userId in userIds:
#                 if userId in subscribe:
#                     if str(senderId) in subscribe[userId]:
#                         subscribe[userId].pop(str(senderId))
#                     if subscribe[userId]=={}:
#                         subscribe.pop(userId)
#             await app.sendFriendMessage(senderId, MessageChain.create(f'已取消订阅{userIds}！'))
        
#         if re.search(r'(\d+:\d+)-(\d+:\d+)', nodisturb) != None and filter(12): # 添加勿扰
#             start, stop = re.search(r'(\d+:\d+)-(\d+:\d+)', nodisturb).groups()
#             nodisturbData = mods.find_one({"name": "mblogSubscribe"})['nodisturb']
#             nodisturbData[str(senderId)] = {"type": "friend", "start": Time.timefomart(start), "stop": Time.timefomart(stop)}
#             mods.update_one({"name": "mblogSubscribe"}, {"$set": {"nodisturb": nodisturbData}})
#             await app.sendFriendMessage(senderId, MessageChain.create(f'已添加勿扰时段:{nodisturb}'))

#     mods.update_one({"name": "mblogSubscribe"}, {"$set": {"blackList": blackList}})
#     mods.update_one({"name": "mblogSubscribe"}, {"$set": {"subscribe": subscribe}})
    