from distutils.log import info
import re
from urllib import response
from aip import AipImageClassify
import json, re
import asyncio

from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend

from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema

channel = Channel.current()

with open("./modules/ImageClassify/config.json",'r') as load_f:
    datainfo = json.load(load_f)
client = AipImageClassify(datainfo['APP_ID'], datainfo['API_KEY'], datainfo['SECRET_KEY'])

@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def friend_message_listener(app: Ariadne, friend: Friend, message: MessageChain):
    session = get_running(Adapter).session
    imgurl = re.findall(r'"url":"(.*?)"', message.asPersistentString())[0]
    async with session.get(imgurl) as r:
        data = await r.read()
        send = client.advancedGeneral(data)['result'][0]
        response = f'''图片识别结果:
        关键词：{send['keyword']}
        准确度：{send['score']*100}%
        标  签：{send['root']}'''
    await app.sendMessage(friend, MessageChain.create(response))
