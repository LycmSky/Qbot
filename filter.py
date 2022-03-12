from turtle import pen
import database

mods = database.databaseInit('mods')

class Filter:
    def __init__(self, mod_name=False, event=False):
        '''进行条件判断：
            mod_name --> mod的名字
            event --> 消息的event对象
        '''
        self.mod_name = mod_name
        self.event = event
    
    def main(self, code: int):
        '''主函数，调用其他函数：
            cede => int 解析为二进制（如0100011)，控制启用哪些判断
            #1 enable --> 确认模块是否开启
            #2 state --> 确认用户是否开启功能
            #3 blacklist --> 确认用户是否被拉黑
            #4 admin --> 确认用户是否为管理员
            '''
        code_b = "{0:b}".format(code)
        funcList = [
            self._enable,       # 0 
            self._state,        # 1
            self._blacklist,    # 2
            self._admin         # 3
            ]
        i, r = 0, True
        if len(code_b) == len(funcList):
            pass
        elif len(code_b) < len(funcList):
            code_b = "0" *(len(funcList) - len(code_b)) + code_b
        else:
            raise Exception("code长度错误")
        while i<len(code_b):
            if int(code_b[i]):
                r = funcList[i]() and r
                i += 1
            else:
                i += 1
                continue
        return r

    def _enable(self):
        '''确认模组总开关状态'''
        return mods.find_one({"name": self.mod_name})["enabled"]

    def _state(self):
        '''确认模组开关状态'''
        blacklist = mods.find_one({"name": self.mod_name})["blackList"]
        if self.event.type == "GroupMessage":
            return False if self.event.sender.group.id in blacklist['Groups'] else True
        elif self.event.type == "FriendMessage":
            return False if self.event.sender.id in blacklist['Friends'] else True

    def _blacklist(self):
        '''确认用户是否存在于模组黑名单'''
        blacklist = mods.find_one({"name": self.mod_name})["blackList"]
        if str(self.event.sender.group.id) in blacklist:
            if self.event.sender.id in blacklist[str(self.event.sender.group.id)]:
                return False
            else:
                return True
        else:
            return True

    def _admin(self):
        '''确认用户是否为该群管理员'''
        return True if str(self.event.sender.permission) != "MEMBER" else False
