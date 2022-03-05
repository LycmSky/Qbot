from calendar import c
from datetime import datetime
from email import header
import re
from functools import reduce
from urllib import response
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.parser.base import MatchContent
from graia.ariadne.app import Ariadne
from graia.ariadne import get_running
from graia.ariadne.adapter import Adapter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain

# 获取插件实例，添加插件信息
channel = Channel.current()
channel.name("微博监控")
channel.description("获取微博动态")
channel.author("Lycm")

@channel.use(ListenerSchema(
    listening_events=[GroupMessage], 
    decorators=[
        MatchContent(".微博")]
))
async def imageClassify(app: Ariadne, group: Group, member: Member, message: MessageChain):
    uid = 1669879400
    imgurl = (f"https://m.weibo.cn/api/container/getIndex?&containerid=107603{uid}")
    session = get_running(Adapter).session
    async with session.get(imgurl) as r:
        imgBase = await r.json()
        mblog = imgBase['data']['cards'][1]['mblog']
        text = re.sub(r'<[^>]+>', '', mblog['text'])
        screen_name = mblog['user']['screen_name']
        scheme = imgBase['data']['cards'][1]['scheme']
        created_at = mblog['created_at']

    response_header = f'''{datetime.strptime(created_at, '%a %b %d %H:%M:%S +0800 %Y')}
    {screen_name}（{uid}）发布了新微博：
    {text}
    '''
    response_footer = f'''
    原帖链接：{scheme}
    '''
    if mblog['pic_num']:
        MessageChain_pic = map(lambda x: MessageChain.create(Image(url=x['url'])), mblog['pics'])
        response = reduce(lambda x, y: x+y, MessageChain_pic, MessageChain.create(response_header))+response_footer
        await app.sendGroupMessage(group, response)
    else:
        await app.sendGroupMessage(group, MessageChain.create(response_header+response_footer))