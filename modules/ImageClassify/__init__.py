import json, re
from tokenize import group
import database
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.parser.base import MatchContent, DetectPrefix, ContainKeyword
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt import InterruptControl
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from distutils.log import info
from aip import AipImageClassify
from graia.broadcast.builtin.decorators import Depend
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.element import Plain

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("识图")
channel.description("通过百度api识别图片")
channel.author("Lycm")

# 读取配置文件，获取百度开放平台api创建实例
with open("./modules/ImageClassify/config.json",'r') as load_f:
    datainfo = json.load(load_f)
client = AipImageClassify(datainfo['APP_ID'], datainfo['API_KEY'], datainfo['SECRET_KEY'])

# 链接数据库
mods = database.databaseInit('mods')
groups = database.databaseInit('groups')

# 条件筛选
# 判断是否开启
def check_state():
    async def check_state_deco(app: Ariadne):
        if not mods.find_one({"name": "ImageClassify"})["enabled"]:
            raise ExecutionStop
    return Depend(check_state_deco)

def check_blacklist():
    async def check_blacklist_deco(app: Ariadne, group: Group, member: Member):
        checkGroup = group.id in mods.find_one({"name": "ImageClassify"})["groupBlackList"]
        checkmMmber = member.id in mods.find_one({"name": "ImageClassify"})["friendBlackList"]
        if checkGroup or checkmMmber:
            raise ExecutionStop
    return Depend(check_blacklist_deco)

def check_admin():
    async def check_admin_deco(app: Ariadne, group: Group, member: Member):
        if member.id not in groups.find_one({"groupId": group.id})['groupAdmin']:
            raise ExecutionStop
    return Depend(check_admin_deco)

# 创建消息处理器，接收群消息中的 .识图 命令
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        MatchContent(".识图"),
        check_state(),
        check_blacklist()]
))
async def imageClassify(app: Ariadne, group: Group, member: Member, message: MessageChain):
    inc = InterruptControl(app.broadcast) # 创建实例
    await app.sendGroupMessage(group, MessageChain.create('请发送图片'))
    # 交互等待函数
    @Waiter.create_using_function([GroupMessage])
    async def waiter(g: Group, m: Member, msg: MessageChain):
        # 判断新消息的群组和用户是否和上文相同，相同则继续。否则结束。
        if group.id == g.id and member.id == m.id:
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
    await app.sendGroupMessage(group, MessageChain.create(responseMsg))

# 启用模组
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[DetectPrefix(".识图"), ContainKeyword(keyword="-开启"), check_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    mods.update_one({"name": "ImageClassify"}, {"$set": {"enabled": True}})
    await app.sendGroupMessage(group, MessageChain.create('已开启识图功能'))

# 停用模组
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[DetectPrefix(".识图"), ContainKeyword(keyword="-关闭"), check_state(), check_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    mods.update_one({"name": "ImageClassify"}, {"$set": {"enabled": False}})
    await app.sendGroupMessage(group, MessageChain.create('已关闭识图功能'))

# 将用户加入黑名单
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[DetectPrefix(".识图"), ContainKeyword(keyword="-拉黑"), check_state(), check_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    print (message.asDisplay())
    userId = int(re.search(r'-拉黑 @?(\d+)', message.asDisplay()).group(1))
    friendBlackList = mods.find_one({"name": "ImageClassify"})['friendBlackList']
    if friendBlackList.count(userId):
        await app.sendGroupMessage(group, MessageChain.create('这家伙早就已经被拉黑了！'))
    else:
        friendBlackList.append(userId)
        mods.update_one({"name": "ImageClassify"}, {"$set": {"friendBlackList": friendBlackList}})
        await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}加入黑名单！'))

# 将用户移出黑名单
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[DetectPrefix(".识图"), ContainKeyword(keyword="-取消拉黑"), check_state(), check_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    userId = int(re.search(r'-取消拉黑 @?(\d+)', message.asDisplay()).group(1))
    friendBlackList = mods.find_one({"name": "ImageClassify"})['friendBlackList']
    if friendBlackList.count(userId):
        friendBlackList.remove(userId)
        mods.update_one({"name": "ImageClassify"}, {"$set": {"friendBlackList": friendBlackList}})
        await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}移出黑名单！'))
    else:
        await app.sendGroupMessage(group, MessageChain.create('小黑屋里没有这个人哦~'))