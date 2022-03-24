from ast import Str
import time
from urllib import response
import aiohttp
import asyncio
import json

class API:
    def __init__(self, key) -> None:
        self.key = key

    async def hourly(self, location, start=0, hours=3) -> Str:
        api_hourly = "https://api.seniverse.com/v3/weather/hourly.json"
        params = {'key': self.key, "location": location, "start": start, "hours": hours}  
        async with aiohttp.ClientSession() as session:
            async with session.get(api_hourly, params=params) as res:
                hourly = await res.json()
                city = hourly['results'][0]['location']['name']
                response = f"{city}未来{hours}小时天气："
                for i in hourly['results'][0]['hourly']:
                    timeArray = time.strptime(i['time'], "%Y-%m-%dT%H:%M:%S+08:00")
                    otherStyleTime = time.strftime("%m/%d  %H时:", timeArray)
                    response += f"\n{otherStyleTime}"
                    response += f"\n    天气：{i['text']}"
                    response += f"\n    气温：{i['temperature']}°"
                    response += f"\n    湿度：{i['humidity']}%"
                    response += f"\n    风向：{i['wind_direction']}"
                    response += f"\n    风速：{i['wind_speed']}km/h"
                return response
            
    async def alarm(self, location: str, id_list: list):
        api_alarm = "https://api.seniverse.com/v3/weather/alarm.json"
        params = {'key': self.key, 'detail': 'more'}
        response = "气象预警信息："
        async with aiohttp.ClientSession() as session:
            async with session.get(api_alarm, params=params) as res:
                alarms = await res.json()
                for alarm in alarms['results']:
                    if location in alarm['location']['path'] and alarm['alarms'][0]['alarm_id'] not in id_list:
                        response += f"\n\n{alarm['alarms'][0]['description']}"
                        id_list.append(alarm['alarms'][0]['alarm_id'])
                return response, id_list



if __name__ == "__main__":
    async def test():
        api = API('SK0rkwg64J1b3JuGG')
        a = await api.alarm("武汉", [])
        print (a)

    loop = asyncio.get_event_loop()
    task = loop.create_task(test())
    loop.run_until_complete(task)