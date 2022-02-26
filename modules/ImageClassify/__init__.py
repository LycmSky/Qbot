from distutils.log import info
import re
from urllib import response
from aip import AipImageClassify
import json, re
import asyncio
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

# 获取插件实例
channel = Channel.current()
channel.name("识图")
channel.description("通过百度api识别图片")
channel.author("Lycm")

# 读取配置文件
with open("./modules/ImageClassify/config.json",'r') as load_f:
    datainfo = json.load(load_f)
client = AipImageClassify(datainfo['APP_ID'], datainfo['API_KEY'], datainfo['SECRET_KEY'])

@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[MatchContent(".识图")]
))
async def friend_message_listener(app: Ariadne, group: Group, member: Member, message: MessageChain):
    inc = InterruptControl(app.broadcast)
    await app.sendGroupMessage(group, MessageChain.create('请发送图片'))

    @Waiter.create_using_function([GroupMessage])
    async def setu_tag_waiter(g: Group, m: Member, msg: MessageChain):
        if group.id == g.id and member.id == m.id:
            return msg

    a = await inc.wait(setu_tag_waiter)
    session = get_running(Adapter).session
    imgurl = re.findall(r'"url":"(.*?)"', a.asPersistentString())[0]
    async with session.get(imgurl) as r:
        data = await r.read()
        send = client.advancedGeneral(data)['result'][0]
        response = f'''图片识别结果:
        关键词：{send['keyword']}
        准确度：{send['score']*100}%
        标  签：{send['root']}'''
    await app.sendGroupMessage(group, MessageChain.create(response))
