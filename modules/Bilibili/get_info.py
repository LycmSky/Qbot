from typing import Dict
from public.tools import Time
import aiohttp
import re

class API:
    def __init__(self) -> None:
        pass

    async def get_season(self, id: str) -> str:
        '''
        获取专栏信息

        id --> 剧集epid 或 ssid
        '''
        url = "http://api.bilibili.com/pgc/view/web/season"
        params = {"season_id": id[2:]} if id[:2]=="ss" else {"ep_id": id[2:]}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response_info:
                info =  await response_info.json()
        if info["code"] != 0:
            return "查询失败"
        typeList = [None, "番剧", "电影", "纪录片", "国创", "电视剧", None, "综艺"]
        地区 = info["result"]["areas"][0]["name"]
        简介 = info["result"]["evaluate"]
        更新信息 = info["result"]["new_ep"]["desc"]
        发布时间 = info["result"]["publish"]["pub_time_show"]
        剧集标题 = info["result"]["season_title"]
        播放页面 = info["result"]["share_url"]
        集数 = info["result"]["total"]
        类型 = typeList[info["result"]["type"]]
        return f"{剧集标题}\n"\
                f"\n简介：{简介}\n\n"\
                f"类型：{类型}  地区：{地区}\n"\
                f"更新信息：{更新信息}\n"\
                f"发布时间：{发布时间}\n\n"\
                f"链接：{播放页面}\n"\

    async def get_userinfo(self, uid: Dict[int, str]) -> str:
        '''
        获取用户信息

        uid --> 用户uid
        '''
        url_info = "https://api.bilibili.com/x/space/acc/info" # 基本信息
        url_navnum = "https://api.bilibili.com/x/space/navnum" # 投稿数据
        params = {'mid': uid}  
        async with aiohttp.ClientSession() as session:
            async with session.get(url_info, params=params) as response_info:
                info =  await response_info.json()
                if info["code"] !=0 :
                    return f"uid:{uid},查无此人"
            async with session.get(url_navnum, params=params) as response_navnum:
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

    async def get_videoinfo(self, bvid: str) -> str:
        '''
        获取视频信息

        bvid --> 视频bv号
        '''
        url = "http://api.bilibili.com/x/web-interface/view"
        params = {'bvid': bvid}  
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as res:
                info =  await res.json()
        desc = info['data']['desc'].replace("\n", "\n    ")
        if info["code"]!=0:
            return "获取失败"
        return f"视频标题：\n"\
                f"    {info['data']['title']}\n"\
                f"\n发布时间：\n"\
                f"    {await Time.stamp_to_date(info['data']['pubdate'])}\n"\
                f"\n其他信息：\n"\
                f"    UP主：{info['data']['owner']['name']}\n"\
                f"    分P数量：{info['data']['videos']}\n"\
                f"    视频时长：{await Time.stamp_to_duration(info['data']['duration'])}\n"\
                f"    视频分区：{info['data']['tname']}\n"\
                f"    BV号：{info['data']['bvid']}\n"\
                f"\n视频简介：\n"\
                f"    {desc}\n"\
                f"\n视频链接：\n"\
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