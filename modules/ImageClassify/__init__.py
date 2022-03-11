import json, re
import database
from filter import Filter
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.saya import Channel
from aip import AipImageClassify
from graia.ariadne.message.commander import Commander, Slot, Arg
from graia.ariadne.message.commander.saya import  CommandSchema

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

async def imageClassify(imgurl):
    '''传入图片链接，返回识图结果'''
    session = get_running(Adapter).session
    async with session.get(imgurl) as r:
        info = client.advancedGeneral(await r.read())['result'][0]
        responseMsg = '图片识别结果:\n关键词：{}\n准确度：{}%\n标  签：{}'
        return responseMsg.format(info['keyword'], info['score']*100, info['root'])

@channel.use(
        CommandSchema(
        ".识图",
        {"open": Arg("[--on|-O|-开启]", bool, False), 
        "close": Arg("[--off|-C|-关闭]", bool, False),
        "black": Arg("[--black|-B|-拉黑] {}", str, ""),
        "white": Arg("[--white|-W|-取消拉黑] {}", str, "")}))
async def control(open, close, black, white, app: Ariadne, event:MessageEvent, message: MessageChain):
    filter = Filter(mod_name="ImageClassify", event=event).main
    senderID = event.sender.id
    blackList = mods.find_one({"name": "ImageClassify"})['blackList']
    # 处理群消息
    if event.type=="GroupMessage":
        groupId = event.sender.group.id

        if open==close==False and black==white=="" and filter(14): # 识图
            inc = InterruptControl(app.broadcast) # 创建实例
            await app.sendGroupMessage(groupId, MessageChain.create('请发送图片'))
            @Waiter.create_using_function([GroupMessage])
            async def waiter(e: MessageEvent, msg: MessageChain):
                '''判断新消息的群组和用户是否和上文相同，相同则继续。否则结束。'''
                if senderID == e.sender.id and groupId == e.sender.group.id:
                    return msg
            # 处理图片消息，获取图片的url
            imginfo = await inc.wait(waiter)
            imgurl = re.findall(r'"url":"(.*?)"', imginfo.asPersistentString())[0]
            responseMsg = await imageClassify(imgurl)
            await app.sendGroupMessage(groupId, MessageChain.create(responseMsg))

        if open and filter(9): # 开启
            if blackList['Groups'].count(groupId):
                blackList['Groups'].remove(groupId)
                await app.sendGroupMessage(groupId, MessageChain.create('已开启识图功能'))

        if close and filter(13): # 关闭
            if not blackList['Groups'].count(groupId):
                blackList['Groups'].append(groupId)
                await app.sendGroupMessage(groupId, MessageChain.create('已关闭识图功能'))

        if black !="" and filter(13): # 拉黑
            userId = list(map(lambda x: int(x), re.findall(r'(\d+)', black)))
            blackList[str(groupId)] = blackList[str(groupId)] if str(groupId) in blackList else []
            blackList[str(groupId)] = list(set(blackList[str(groupId)] +  userId))
            await app.sendGroupMessage(groupId, MessageChain.create(f'已将{userId}加入黑名单！'))

        if white !="" and filter(13): # 取消拉黑
            userId = list(map(lambda x: int(x), re.findall(r'(\d+)', white)))
            blackList[str(groupId)] = blackList[str(groupId)] if str(groupId) in blackList else []
            blackList[str(groupId)] = list(set(blackList[str(groupId)]) -  set(userId))
            await app.sendGroupMessage(groupId, MessageChain.create(f'已将{userId}移出黑名单！'))

    # 处理好友消息
    elif event.type=="FriendMessage":
        if open==close==False and black==white=="" and filter(12): # 识图
            inc = InterruptControl(app.broadcast) # 创建实例
            await app.sendFriendMessage(senderID, MessageChain.create('请发送图片'))
            @Waiter.create_using_function([FriendMessage])
            async def waiter(e: MessageEvent, msg: MessageChain):
                '''判断新消息的群组和用户是否和上文相同，相同则继续。否则结束。'''
                if senderID == e.sender.id:
                    return msg
            # 处理图片消息，获取图片的url
            imginfo = await inc.wait(waiter)
            imgurl = re.findall(r'"url":"(.*?)"', imginfo.asPersistentString())[0]
            responseMsg = await imageClassify(imgurl)
            await app.sendFriendMessage(senderID, MessageChain.create(responseMsg))

        if open and filter(8): # 开启
            if blackList['Friends'].count(event.sender.id):
                blackList['Friends'].remove(event.sender.id)
                await app.sendFriendMessage(event.sender.id, MessageChain.create('已开启识图功能'))

        if close and filter(12): # 关闭
            if not blackList['Friends'].count(event.sender.id):
                blackList['Friends'].append(event.sender.id)
                await app.sendFriendMessage(event.sender.id, MessageChain.create('已关闭识图功能'))

    # 更新数据库
    mods.update_one({"name": "ImageClassify"}, {"$set": {"blackList": blackList}})