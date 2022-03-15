import asyncio
import os, json
from graia.ariadne.app import Ariadne
from graia.ariadne.model import MiraiSession
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler.saya import GraiaSchedulerBehaviour, SchedulerSchema
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour, SchedulerSchema
from graia.scheduler import GraiaScheduler
from graia.scheduler import timers
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.commander.saya import CommanderBehaviour, CommandSchema
from graia.ariadne.message.commander import Commander, Slot, Arg

with open("./config.json",'r') as load_f:
    datainfo = json.load(load_f)['MiraiSession']

# 创建 Ariadne 实例
app = Ariadne(
    MiraiSession(
        host=datainfo['host'],
        verify_key=datainfo['verify_key'],
        account=datainfo['account'],
    ),
)

broadcast = app.broadcast

cmd = Commander(broadcast)
# 创建 saya 实例
saya = app.create(Saya)
saya.install_behaviours(
    app.create(BroadcastBehaviour), 
    GraiaSchedulerBehaviour(app.create(GraiaScheduler)),
    CommanderBehaviour(cmd)
)

# 使用 saya 导入 modules 文件夹下的模组
with saya.module_context():
    for module in  os.listdir('./modules'):
        saya.require(f'modules.{module}') if os.path.isdir(f'./modules/{module}') else None

# 以阻塞方式启动 Ariadne 并等待其停止.
app.launch_blocking()