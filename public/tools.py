import re
import time
from functools import wraps

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

