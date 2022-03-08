from array import array
from ast import List
from fileinput import close
import json, re
import database, criteria
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.parser.base import MatchContent, DetectPrefix, ContainKeyword
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt import InterruptControl
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from aip import AipImageClassify
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.commander import Commander, Slot, Arg
from graia.ariadne.message.commander.saya import CommanderBehaviour, CommandSchema

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("识图")
channel.description("通过百度api识别图片")
channel.author("Lycm")

# 读取配置文件，获取百度开放平台api创建实例
with open("./config.json",'r') as load_f:
    datainfo = json.load(load_f)
client = AipImageClassify(datainfo['ImageClassify']['APP_ID'], datainfo['ImageClassify']['API_KEY'], datainfo['ImageClassify']['SECRET_KEY'])

# 链接数据库
mods = database.databaseInit('mods')
if mods.find_one({"name": "ImageClassify"}) == None:
    mods.insert_one({
        "name": "ImageClassify",
        "enabled": True,
        "blackList": {
            "Friends": [],
            "Groups": []
        },
        "whiteList": [],
        })


# 创建消息处理器，接收群消息中的 .识图 命令
@channel.use(
    ListenerSchema(
    listening_events=[GroupMessage, FriendMessage], 
    decorators=[
        MatchContent(".识图"),
        criteria.check_mod_state("ImageClassify"),
        criteria.check_mod_blacklist("ImageClassify")]
))
async def imageClassify(app: Ariadne, event:MessageEvent , message: MessageChain):
    print (event)
    sender = event.sender
    inc = InterruptControl(app.broadcast) # 创建实例
    send = app.sendFriendMessage if event.type=="FriendMessage" else app.sendGroupMessage
    await send(sender, MessageChain.create('请发送图片'))
    # 交互等待函数
    @Waiter.create_using_function([GroupMessage, FriendMessage])
    async def waiter(e: MessageEvent, msg: MessageChain):
        # 判断新消息的群组和用户是否和上文相同，相同则继续。否则结束。
        print (e)
        if sender.id == e.sender.id and event.type == e.type:
            return msg

    # 处理图片消息，获取图片的url
    imginfo = await inc.wait(waiter)
    imgurl = re.findall(r'"url":"(.*?)"', imginfo.asPersistentString())[0]
    # 通过图片url获取图片二进制编码，并传入识图实例
    session = get_running(Adapter).session
    async with session.get(imgurl) as r:
        imgBase = await r.read()
        info = client.advancedGeneral(imgBase)['result'][0]
        responseMsg = f'''图片识别结果:
        关键词：{info['keyword']}
        准确度：{info['score']*100}%
        标  签：{info['root']}'''
    await send(sender, MessageChain.create(responseMsg))

# 启用模组
@channel.use(
        CommandSchema(
        "[command|命令]",
        {
            "open": Arg("[--on|-O|-开启]", bool, False), 
            "close": Arg("[--off|-C|-关闭]", bool, False),
            "black": Arg("[--black|-B|-拉黑] {}", str, ""),
            "white": Arg("[--white|-W|-取消拉黑] {}", str, "")
        },
    )
)
async def control(open, close, black, white, app: Ariadne, event:MessageEvent, message: MessageChain):
    print (open, close, black, white)
    print (message)
    if open: # 开启
        blackList = mods.find_one({"name": "ImageClassify"})['blackList']
        if event.type=="GroupMessage" and event.sender.permission != "MEMBER":
            if blackList['Groups'].count(event.sender.group.id):
                blackList['Groups'].remove(event.sender.group.id)
                mods.update_one({"name": "ImageClassify"}, {"$set": {"blackList": blackList}})
                await app.sendGroupMessage(event.sender.group.id, MessageChain.create('已开启识图功能'))
        elif event.type=="FriendMessage":
            if blackList['Friends'].count(event.sender.id):
                blackList['Friends'].remove(event.sender.id)
                mods.update_one({"name": "ImageClassify"}, {"$set": {"blackList": blackList}})
                await app.sendFriendMessage(event.sender.id, MessageChain.create('已开启识图功能'))

    if close: # 关闭
        blackList = mods.find_one({"name": "ImageClassify"})['blackList']  
        if event.type=="GroupMessage" and event.sender.permission != "MEMBER":
            if not blackList['Groups'].count(event.sender.group.id):
                blackList['Groups'].append(event.sender.group.id)
                mods.update_one({"name": "ImageClassify"}, {"$set": {"blackList": blackList}})
                await app.sendGroupMessage(event.sender.group.id, MessageChain.create('已关闭识图功能'))
        elif event.type=="FriendMessage":
            if not blackList['Friends'].count(event.sender.id):
                blackList['Friends'].append(event.sender.id)
                mods.update_one({"name": "ImageClassify"}, {"$set": {"blackList": blackList}})
                await app.sendFriendMessage(event.sender.id, MessageChain.create('已关闭识图功能'))


# 将用户加入黑名单
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        DetectPrefix(".识图"), 
        ContainKeyword(keyword="-拉黑"), 
        criteria.check_mod_blacklist("ImageClassify"),
        criteria.check_mod_state("ImageClassify")]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    criteria.check_group_admin(member.permission)
    userId = list(map(lambda x: int(x), re.findall(r'@(\d+)', message.asDisplay())))
    blackList = mods.find_one({"name": "ImageClassify"})['blackList']
    blackList = list(set(blackList +  userId))
    mods.update_one({"name": "ImageClassify"}, {"$set": {"blackList": blackList}})
    await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}加入黑名单！'))

# 将用户移出黑名单
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        DetectPrefix(".识图"), 
        ContainKeyword(keyword="-取消拉黑"), 
        criteria.check_mod_blacklist("ImageClassify"),
        criteria.check_mod_state("ImageClassify")]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    criteria.check_group_admin(member.permission)
    userId = list(map(lambda x: int(x), re.findall(r'@(\d+)', message.asDisplay())))
    blackList = mods.find_one({"name": "ImageClassify"})['blackList']
    blackList = list(set(blackList) -  set(userId))
    mods.update_one({"name": "ImageClassify"}, {"$set": {"blackList": blackList}})
    await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}移出黑名单！'))