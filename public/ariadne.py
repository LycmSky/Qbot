from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.parser.twilight import Twilight




class Bot:
    def __init__(self, app: Ariadne, event: MessageEvent) -> None:
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