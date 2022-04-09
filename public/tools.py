import re
import time
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.parser.twilight import Twilight

class Time:
    def __init__(self) -> None:
        pass

    async def stamp_to_date(timeStamp):
        timeArray = time.localtime(timeStamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

    async def stamp_to_duration(timeStamp):
        res = ""
        hour = '%02d' % (timeStamp//3600)
        minute = '%02d' % (timeStamp%3600//60)
        second = '%02d' % (timeStamp%3600%60)
        if timeStamp//3600!=0:
            res += f"{hour}:"
        res += f"{minute}:{second}"
        return res

    def timefomart(timeStr):
        time = re.search(r'(\d+):(\d+)', timeStr)
        if time:
            h, m = time.groups()
            h = int(h) if 0<=int(h)<24 else 0
            m = int(m) if 0<=int(m)<60 else 0
            stamp = h*60 + m
            return stamp

class Bot:
    def __init__(self, app: Ariadne, event:MessageEvent) -> None:
        '''
        功能封装处理
        '''
        self.message_type = event.type

        if event.type=="GroupMessage":
            self.__send = app.sendGroupMessage
            self.sender_id = event.sender.group.id
        elif event.type=="FriendMessage":
            self.__send = app.sendFriendMessage
            self.sender_id = event.sender.id

    async def sendMessage(self, message: MessageChain) -> None:
        '''封装发送消息的函数'''
        await self.__send(self.sender_id, message)