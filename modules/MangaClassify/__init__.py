import re
import database
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.parser.base import MatchContent
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Image
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from distutils.log import info
from graia.broadcast.builtin.decorators import Depend
from graia.broadcast.exceptions import ExecutionStop

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("识番")
channel.description("trace.moe api 识别番剧")
channel.author("Lycm")

# 链接数据库
db = database.databaseInit('mods')

# 条件筛选
# 判断是否开启
def check_state():
    async def check_state_deco(app: Ariadne):
        if not db.find_one({"name": "MangaClassify"})["enabled"]:
            raise ExecutionStop
    return Depend(check_state_deco)

def check_blacklist():
    async def check_blacklist_deco(app: Ariadne, group: Group, member: Member):
        checkGroup = group.id in db.find_one({"name": "MangaClassify"})["groupBlackList"]
        checkmMmber = member.id in db.find_one({"name": "MangaClassify"})["friendBlackList"]
        if checkGroup or checkmMmber:
            raise ExecutionStop
    return Depend(check_blacklist_deco)

# 设置api地址
url = "https://api.trace.moe/search?cutBorders&url={}"

# 创建消息处理器，接收群消息中的 .识番 命令
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        MatchContent(".识番"),
        check_state(),
        check_blacklist()
        ]
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


