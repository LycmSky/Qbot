import json, re
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.parser.base import MatchContent
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

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("识图")
channel.description("通过百度api识别图片")
channel.author("Lycm")

# 读取配置文件，获取百度开放平台api创建实例
with open("./modules/ImageClassify/config.json",'r') as load_f:
    datainfo = json.load(load_f)
client = AipImageClassify(datainfo['APP_ID'], datainfo['API_KEY'], datainfo['SECRET_KEY'])

# 创建消息处理器，接收群消息中的 .识图 命令
@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[MatchContent(".识图")]
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
