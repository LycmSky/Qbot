import json, re
import database, criteria
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
from aip import AipImageClassify


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

# 创建消息处理器，接收群消息中的 .识图 命令
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        MatchContent(".识图"),
        criteria.check_mod_state("ImageClassify"),
        criteria.check_mod_blacklist("ImageClassify")]
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
    decorators=[DetectPrefix(".识图"), ContainKeyword(keyword="-开启"), criteria.check_group_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    mods.update_one({"name": "ImageClassify"}, {"$set": {"enabled": True}})
    await app.sendGroupMessage(group, MessageChain.create('已开启识图功能'))

# 停用模组
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[DetectPrefix(".识图"), ContainKeyword(keyword="-关闭"), criteria.check_mod_state("ImageClassify"), criteria.check_group_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    mods.update_one({"name": "ImageClassify"}, {"$set": {"enabled": False}})
    await app.sendGroupMessage(group, MessageChain.create('已关闭识图功能'))

# 将用户加入黑名单
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[DetectPrefix(".识图"), ContainKeyword(keyword="-拉黑"), criteria.check_mod_state("ImageClassify"), criteria.check_group_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    print (message.asDisplay())
    userId = int(re.search(r'-拉黑 @?(\d+)', message.asDisplay()).group(1))
    blackList = mods.find_one({"name": "ImageClassify"})['blackList']
    if blackList.count(userId):
        await app.sendGroupMessage(group, MessageChain.create(f'{userId}已在黑名单中'))
    else:
        blackList.append(userId)
        mods.update_one({"name": "ImageClassify"}, {"$set": {"blackList": blackList}})
        await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}加入黑名单！'))

# 将用户移出黑名单
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[DetectPrefix(".识图"), ContainKeyword(keyword="-取消拉黑"), criteria.check_mod_state("ImageClassify"), criteria.check_group_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    userId = int(re.search(r'-取消拉黑 @?(\d+)', message.asDisplay()).group(1))
    blackList = mods.find_one({"name": "ImageClassify"})['blackList']
    if blackList.count(userId):
        blackList.remove(userId)
        mods.update_one({"name": "ImageClassify"}, {"$set": {"blackList": blackList}})
        await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}移出黑名单！'))
    else:
        await app.sendGroupMessage(group, MessageChain.create(f'黑名单中不存在{userId}'))