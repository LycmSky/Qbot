from typing import Dict
import aiohttp
import re

class API:
    def __init__(self) -> None:
        pass

    async def get_videoinfo(self, bvid: str) -> str:
        '''
        获取视频信息

        bvid --> 视频bv号
        '''
        url = f"http://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                info =  await res.json()
                return f"Bilibili视频解析：\n"\
                       f"标题：{info['data']['title']}\n"\
                       f"UP主：{info['data']['owner']['name']}\n\n"\
                       f"https://www.bilibili.com/video/{bvid}"


    async def get_bvid(self, url: str) -> str:
        '''
        通过视频链接获取BV号
        '''
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                real_url =  str(res.real_url)
                bvid = re.search(r'BV[\d\w]+', real_url).group()
                return bvid

    async def get_videolist(self, uid: Dict[int, str]) -> dict:
        '''
        获取用户视频列表

        uid --> 用户uid
        '''
        url = "https://api.bilibili.com/x/space/arc/search?mid=3884198&jsonp=jsonp" # 视频列表
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                info =  await res.json()

    async def get_userinfo(self, uid: Dict[int, str]) -> str:
        '''
        获取用户信息

        uid --> 用户uid
        '''
        url_info = f"https://api.bilibili.com/x/space/acc/info?mid={uid}" # 基本信息
        url_navnum = f"https://api.bilibili.com/x/space/navnum?mid={uid}" # 投稿数据
        async with aiohttp.ClientSession() as session:
            async with session.get(url_info) as response_info:
                info =  await response_info.json()
            async with session.get(url_navnum) as response_navnum:
                navnum =  await response_navnum.json()

            official = ["无", "bilibili知名UP主", "大V达人", "企业官方账号", "政府官方账号", "传统媒体及新媒体官方账号", "校园,公益组织,社会团体等官方账号", None, None, "社会知名人士"]
            res =  f"{info['data']['name']}\n\n"\
                   f"uid：{uid}\n"\
                   f"签名：{info['data']['sign']}\n"\
                   f"等级：LV{info['data']['level']}\n"\
                   f"\n投稿：\n"\
                   f"    视频：{navnum['data']['video']}{' '*(7-len(str(navnum['data']['video'])))}音频：{navnum['data']['audio']}\n"\
                   f"    专栏：{navnum['data']['article']}{' '*(7-len(str(navnum['data']['article'])))}相簿：{navnum['data']['album']}\n"\
                   f"\n认证：\n"\
                   f"    认证类型：{official[info['data']['official']['role']]}\n"\
                   f"    认证信息：{info['data']['official']['title']}\n"\
                   f"    认证描述：{info['data']['official']['desc']}\n"
            if info['data']['live_room']!=None:
                res += f"\n直播间：\n"\
                       f"    直播状态：{'正在直播' if info['data']['live_room']['liveStatus'] else '未开播'}\n"\
                       f"    直播间标题：{info['data']['live_room']['title']}\n"\
                       f"    直播间ID：{info['data']['live_room']['roomid']}\n"
            return res