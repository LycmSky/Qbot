from graia.broadcast.builtin.decorators import Depend
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
import database

mods = database.databaseInit('mods')
groups = database.databaseInit('groups')

def check_mod_state(mod_name: str):
    '''确认模组是否为开启状态'''
    async def check_state_deco(app: Ariadne):
        if not mods.find_one({"name": mod_name})["enabled"]:
            raise ExecutionStop
    return Depend(check_state_deco)

def check_mod_blacklist(mod_name: str):
    '''确认用户是否存在于模组黑名单'''
    async def check_blacklist_deco(app: Ariadne, group: Group, member: Member):
        blacklist = mods.find_one({"name": mod_name})["blackList"]
        if group.id in blacklist or member.id in blacklist:
            raise ExecutionStop
    return Depend(check_blacklist_deco)

def check_group_admin():
    '''确认用户是否为该群管理员'''
    async def check_admin_deco(app: Ariadne, group: Group, member: Member):
        if member.id not in groups.find_one({"groupId": group.id})['groupAdmin']:
            raise ExecutionStop
    return Depend(check_admin_deco)