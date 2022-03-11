# import re
# import database, criteria
# from graia.broadcast.interrupt.waiter import Waiter
# from graia.ariadne.message.parser.base import MatchContent, DetectPrefix, ContainKeyword
# from graia.ariadne import get_running
# from graia.ariadne.adapter import Adapter
# from graia.ariadne.app import Ariadne
# from graia.ariadne.event.message import GroupMessage
# from graia.ariadne.message.chain import MessageChain
# from graia.ariadne.model import Group, Member
# from graia.broadcast.interrupt import InterruptControl
# from graia.ariadne.message.element import Image, Plain
# from graia.saya import Channel
# from graia.saya.builtins.broadcast.schema import ListenerSchema
# from graia.broadcast.exceptions import ExecutionStop
# from graia.ariadne.model import MiraiSession

# # 获取插件实例，添加插件信息
# channel = Channel.current()
# channel.name("识番")
# channel.description("trace.moe api 识别番剧")
# channel.author("Lycm")

# # 链接数据库
# mods = database.databaseInit('mods')
# if mods.find_one({"name": "MangaClassify"}) == None:
#     mods.insert_one({
#         "name": "MangaClassify",
#         "enabled": True,
#         "blackList": [],
#         "whiteList": [],
#         })


# # 设置api地址
# url = "https://api.trace.moe/search?cutBorders&url={}"

# # 创建消息处理器，接收群消息中的 .识番 命令
# @channel.use(ListenerSchema(
#     listening_events=[GroupMessage], 
#     decorators=[
#         MatchContent(".识番"),
#         criteria.check_mod_state("MangaClassify"),
#         criteria.check_mod_blacklist("MangaClassify")]))
# async def mangaClassify(app: Ariadne, group: Group, member: Member, message: MessageChain):
#     inc = InterruptControl(app.broadcast) # 创建实例
#     await app.sendGroupMessage(group, MessageChain.create('请发送图片'))
#     # 交互等待函数
#     @Waiter.create_using_function([GroupMessage])
#     async def waiter(g: Group, m: Member, msg: MessageChain):
#         # 判断新消息的群组和用户是否和上文相同，相同则继续。否则结束。
#         if group.id == g.id and member.id == m.id:
#             return msg

#     # 处理图片消息，获取图片的url
#     imginfo = await inc.wait(waiter)
#     imgurl = re.findall(r'"url":"(.*?)"', imginfo.asPersistentString())[0]
#     # 拼接url并发起请求，返回json格式数据
#     session = get_running(Adapter).session
#     async with session.get(url.format(imgurl)) as r:
#             ret = await r.json()
#     ret = ret["result"][0]

#     # 格式化信息
#     responseMsg = f'''番剧识别结果:
#     番剧名：{ret["filename"]}
#     准确度：{int(ret["similarity"]*100)}%
#     集  数：{ret["episode"]}
#     时  间：{int(ret["from"]//60)}分{int(ret["from"]%60)}秒 - {int(ret["to"]//60)}分{int(ret["to"]%60)}秒
#     参考图：'''
#     # 发送结果
#     await app.sendGroupMessage(group, MessageChain.create(responseMsg, Image(url=ret['image'])))

# # 启用模组
# @channel.use(ListenerSchema(
#     listening_events=[GroupMessage], 
#     decorators=[
#         DetectPrefix(".识番"), 
#         ContainKeyword(keyword="-开启"), 
#         criteria.check_mod_state("MangaClassify")]))
# async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
#     criteria.check_group_admin(member.permission)
#     blackList = mods.find_one({"name": "MangaClassify"})['blackList']
#     if blackList.count(group.id):
#         blackList.remove(group.id)
#         mods.update_one({"name": "MangaClassify"}, {"$set": {"blackList": blackList}})
#         await app.sendGroupMessage(group, MessageChain.create('已开启识番功能'))
#     else:
#         await app.sendGroupMessage(group, MessageChain.create('要开启的话得先关闭哦~'))

# # 停用模组
# @channel.use(ListenerSchema(
#     listening_events=[GroupMessage], 
#     decorators=[
#         DetectPrefix(".识番"),
#         ContainKeyword(keyword="-关闭"), 
#         criteria.check_mod_blacklist("MangaClassify"),
#         criteria.check_mod_state("MangaClassify")]))
# async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
#     criteria.check_group_admin(member.permission)
#     blackList = mods.find_one({"name": "MangaClassify"})['blackList']
#     blackList.append(group.id)
#     mods.update_one({"name": "MangaClassify"}, {"$set": {"blackList": blackList}})
#     await app.sendGroupMessage(group, MessageChain.create('已开启识番功能'))

# # 添加用户到黑名单
# @channel.use(ListenerSchema(
#     listening_events=[GroupMessage], 
#     decorators=[
#         DetectPrefix(".识番"),
#         ContainKeyword(keyword="-拉黑"), 
#         criteria.check_mod_blacklist("MangaClassify"),
#         criteria.check_mod_state("MangaClassify")]))
# async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
#     criteria.check_group_admin(member.permission)
#     userId = list(map(lambda x: int(x), re.findall(r'@(\d+)', message.asDisplay())))
#     blackList = mods.find_one({"name": "MangaClassify"})['blackList']
#     blackList = list(set(blackList +  userId))
#     mods.update_one({"name": "MangaClassify"}, {"$set": {"blackList": blackList}})
#     await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}加入黑名单！'))

# # 将用户移出黑名单
# @channel.use(ListenerSchema(
#     listening_events=[GroupMessage], 
#     decorators=[
#         DetectPrefix(".识番"), 
#         ContainKeyword(keyword="-取消拉黑"), 
#         criteria.check_mod_blacklist("MangaClassify"),
#         criteria.check_mod_state("MangaClassify")]))
# async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
#     criteria.check_group_admin(member.permission)
#     userId = list(map(lambda x: int(x), re.findall(r'@(\d+)', message.asDisplay())))
#     blackList = mods.find_one({"name": "MangaClassify"})['blackList']
#     blackList = list(set(blackList) -  set(userId))
#     mods.update_one({"name": "MangaClassify"}, {"$set": {"blackList": blackList}})
#     await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}移出黑名单！'))

from email.mime import image
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
from graia.ariadne.message.commander import Commander, Slot, Arg
from graia.ariadne.message.commander.saya import  CommandSchema
from graia.ariadne.message.element import Image

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("识番")
channel.description("trace.moe api 识别番剧")
channel.author("Lycm")

# 链接数据库
mods = database.databaseInit('mods')
if mods.find_one({"name": "MangaClassify"}) == None:
    mods.insert_one({
        "name": "MangaClassify",
        "enabled": True,
        "blackList": {
            "Friends": [],
            "Groups": []
        },
        "whiteList": [],
        })

async def MangaClassify(imgurl):
    '''传入图片链接，返回识番结果'''
    url = "https://api.trace.moe/search?cutBorders&url={}"
    session = get_running(Adapter).session
    async with session.get(url.format(imgurl)) as r:
            ret = await r.json()
    ret = ret["result"][0]

    # 格式化信息
    responseMsg = f'''番剧识别结果:
    番剧名：{ret["filename"]}
    准确度：{int(ret["similarity"]*100)}%
    集  数：{ret["episode"]}
    时  间：{int(ret["from"]//60)}分{int(ret["from"]%60)}秒 - {int(ret["to"]//60)}分{int(ret["to"]%60)}秒
    参考图：'''
    # 发送结果
    return responseMsg, Image(url=ret['image'])

@channel.use(
        CommandSchema(
        ".识番",
        {"open": Arg("[--on|-O|-开启]", bool, False), 
        "close": Arg("[--off|-C|-关闭]", bool, False),
        "black": Arg("[--black|-B|-拉黑] {}", str, ""),
        "white": Arg("[--white|-W|-取消拉黑] {}", str, "")}))
async def control(open, close, black, white, app: Ariadne, event:MessageEvent, message: MessageChain):
    filter = Filter(mod_name="MangaClassify", event=event).main
    senderID = event.sender.id
    blackList = mods.find_one({"name": "MangaClassify"})['blackList']
    # 处理群消息
    if event.type=="GroupMessage":
        groupId = event.sender.group.id

        if open==close==False and black==white=="" and filter(14): # 识番
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
            responseMsg, image = await MangaClassify(imgurl)
            await app.sendGroupMessage(groupId, MessageChain.create(responseMsg, image))

        if open and filter(9): # 开启
            if blackList['Groups'].count(groupId):
                blackList['Groups'].remove(groupId)
                await app.sendGroupMessage(groupId, MessageChain.create('已开启识番功能'))

        if close and filter(13): # 关闭
            if not blackList['Groups'].count(groupId):
                blackList['Groups'].append(groupId)
                await app.sendGroupMessage(groupId, MessageChain.create('已关闭识番功能'))

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
        if open==close==False and black==white=="" and filter(12): # 识番
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
            responseMsg = await MangaClassify(imgurl)
            await app.sendFriendMessage(event.sender.id, MessageChain.create(responseMsg, image))

        if open and filter(8): # 开启
            if blackList['Friends'].count(event.sender.id):
                blackList['Friends'].remove(event.sender.id)
                await app.sendFriendMessage(event.sender.id, MessageChain.create('已开启识番功能'))

        if close and filter(12): # 关闭
            if not blackList['Friends'].count(event.sender.id):
                blackList['Friends'].append(event.sender.id)
                await app.sendFriendMessage(event.sender.id, MessageChain.create('已关闭识番功能'))

    # 更新数据库
    mods.update_one({"name": "MangaClassify"}, {"$set": {"blackList": blackList}})