import re
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
from graia.ariadne.message.element import Image, Plain
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("识番")
channel.description("trace.moe api 识别番剧")
channel.author("Lycm")

# 链接数据库
mods = database.databaseInit('mods')

# 设置api地址
url = "https://api.trace.moe/search?cutBorders&url={}"

# 创建消息处理器，接收群消息中的 .识番 命令
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        MatchContent(".识番"),
        criteria.check_mod_state("MangaClassify"),
        criteria.check_mod_blacklist("MangaClassify")]))
async def mangaClassify(app: Ariadne, group: Group, member: Member, message: MessageChain):
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
    # 拼接url并发起请求，返回json格式数据
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
    await app.sendGroupMessage(group, MessageChain.create(responseMsg, Image(url=ret['image'])))

# 启用模组
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[DetectPrefix(".识番"), ContainKeyword(keyword="-开启"), criteria.check_group_admin]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    mods.update_one({"name": "MangaClassify"}, {"$set": {"enabled": True}})
    await app.sendGroupMessage(group, MessageChain.create('已开启识番功能'))

# 停用模组
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        DetectPrefix(".识番"),
        ContainKeyword(keyword="-关闭"),
        criteria.check_mod_state("MangaClassify"), 
        criteria.check_group_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    mods.update_one({"name": "MangaClassify"}, {"$set": {"enabled": False}})
    await app.sendGroupMessage(group, MessageChain.create('已关闭识番功能'))

# 添加用户到黑名单
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        DetectPrefix(".识番"),
        ContainKeyword(keyword="-拉黑"),
        criteria.check_mod_state("MangaClassify"),
        criteria.check_group_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    print (message.asDisplay())
    userId = int(re.search(r'-拉黑 @?(\d+)', message.asDisplay()).group(1))
    blackList = mods.find_one({"name": "MangaClassify"})['blackList']
    if blackList.count(userId):
        await app.sendGroupMessage(group, MessageChain.create(f'{userId}已在黑名单中'))
    else:
        blackList.append(userId)
        mods.update_one({"name": "MangaClassify"}, {"$set": {"blackList": blackList}})
        await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}加入黑名单！'))

# 将用户移出黑名单
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        DetectPrefix(".识番"), 
        ContainKeyword(keyword="-取消拉黑"), 
        criteria.check_mod_state("MangaClassify"), 
        criteria.check_group_admin()]))
async def control(app: Ariadne, group: Group, member: Member, message: MessageChain):
    userId = int(re.search(r'-取消拉黑 @?(\d+)', message.asDisplay()).group(1))
    blackList = mods.find_one({"name": "MangaClassify"})['blackList']
    if blackList.count(userId):
        blackList.remove(userId)
        mods.update_one({"name": "MangaClassify"}, {"$set": {"blackList": blackList}})
        await app.sendGroupMessage(group, MessageChain.create(f'已将{userId}移出黑名单！'))
    else:
        await app.sendGroupMessage(group, MessageChain.create(f'黑名单中不存在{userId}'))