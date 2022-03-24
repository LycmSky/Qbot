from email.policy import default
import database

from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.parser.twilight import Twilight

data_template = {
    "name": "Weather",
    "enabled": {
        "state": True,
        "c_friends": [],
        "c_groups": []
    },
    "subscribe": {}
}

user_template = {
    "type": "",
    "location": "上海",
    "start": 0,
    "hours": 3,
    "days": 1
}

class Command:
    def __init__(self, app: Ariadne, event:MessageEvent) -> None:
        self.mods = database.databaseInit('mods')
        self.mods.insert_one(data_template) if self.mods.find_one({"name": "Weather"})==None else None
        self.data = self.mods.find_one({"name": "Weather"})
        self.type = event.type

        if event.type=="GroupMessage":
            self.__send = app.sendGroupMessage
            self.sender_id = event.sender.group.id
        elif event.type=="FriendMessage":
            self.__send = app.sendFriendMessage
            self.sender_id = event.sender.id


        if self.sender_id not in self.data["subscribe"]:
            self.data["subscribe"][str(self.sender_id)] = user_template
            self.data["subscribe"][str(self.sender_id)]["type"] = event.type[:-7]

        self.user_data = self.data["subscribe"][str(self.sender_id)]

    async def sendMessage(self, message: MessageChain) -> None:
        '''封装发送消息的函数'''
        await self.__send(self.sender_id, message)

    async def switch(self, switch: bool) -> None:
        '''开关功能'''
        if self.type=="GroupMessage":
            if switch and self.data["enabled"]["c_groups"].count(self.sender_id):
                self.data["enabled"]["c_groups"].remove(self.sender_id)
            elif not switch and not self.data["enabled"]["c_groups"].count(self.sender_id):
                self.data["enabled"]["c_groups"].append(self.sender_id)
        elif self.type=="FriendMessage":
            if switch and self.data["enabled"]["c_friends"].count(self.sender_id):
                self.data["enabled"]["c_friends"].remove(self.sender_id)
            elif not switch and not self.data["enabled"]["c_friends"].count(self.sender_id):
                self.data["enabled"]["c_friends"].append(self.sender_id)

        state = "开启" if switch else "关闭"
        await self.sendMessage(MessageChain.create(f"已{state}天气功能"))
        self.__del__()
        raise ExecutionStop

    async def help(self, twilight: Twilight) -> None:
        '''帮助功能'''
        await self.sendMessage(MessageChain.create(twilight.get_help("用法字符串", "描述", "总结")))
        self.__del__()
        raise ExecutionStop

    def __del__(self) -> None:
        self.mods.update_one({"name": "Weather"}, {'$set': self.data})
