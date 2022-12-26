import aiohttp, re
from datetime import datetime
from time import mktime, time
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.parser.twilight import Twilight
from graia.ariadne.message.chain import MessageChain
from public.ariadne import Bot
from public.database import Database
from functools import reduce

class Info:
    def __init__(self) -> None:
        pass

    async def get_last_blog(self, uid: dict[str, int]) -> dict:
        '''获取目标最新微博信息'''
        # 请求数据
        api = f"https://m.weibo.cn/api/container/getIndex?&containerid=107603{uid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api) as res:
                response =  await res.json()
        
        # 提取最新一条动态
        first_card_time = int(mktime(datetime.strptime(response['data']['cards'][0]['mblog']['created_at'], '%a %b %d %H:%M:%S +0800 %Y').timetuple()))
        second_card_time = int(mktime(datetime.strptime(response['data']['cards'][1]['mblog']['created_at'], '%a %b %d %H:%M:%S +0800 %Y').timetuple()))
        top = 0 if first_card_time > second_card_time else 1
        mblog = response['data']['cards'][top]['mblog']
        return {
            "uid": uid,  # 用户ID
            "time": datetime.strptime(mblog['created_at'], '%a %b %d %H:%M:%S +0800 %Y'),  # 发布时间
            "scheme": response['data']['cards'][top]['scheme'],  # 链接
            "text": re.sub(r'<[^>]+>', '', mblog['text']),  # 内容
            "screen_name": mblog['user']['screen_name'],  # 用户名
            "id": mblog['id'],  # 微博ID
            "pics": mblog['pics'] if 'pics' in mblog else None # 是否有图片
        }

class Control:
    def __init__(self, database: Database, bot: Bot) -> None:
        self.type = bot.message_type
        self.sender_id = bot.sender_id
        self.sendMessage = bot.sendMessage

        self.data = database.data
        self.update = database.update

    async def help(self, twilight: Twilight) -> None:
        '''帮助功能'''
        await self.sendMessage(MessageChain.create(twilight.get_help("用法字符串", "描述", "总结")))

    async def switch(self, switch: bool) -> None:
        '''开关功能'''
        if switch and self.data["enabled"][self.type[:-7]].count(self.sender_id):
            self.data["enabled"][self.type[:-7]].remove(self.sender_id)
        elif not switch and not self.data["enabled"][self.type[:-7]].count(self.sender_id):
            self.data["enabled"][self.type[:-7]].append(self.sender_id)
        state = "开启" if switch else "关闭"
        await self.sendMessage(MessageChain.create(f"已{state}功能"))
        self.update("enabled", self.data["enabled"])

    async def uid_list_add(self, id_list):
        pass