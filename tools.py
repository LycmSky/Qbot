import re

def timefomart(timeStr):
    time = re.search(r'(\d+):(\d+)', timeStr)
    if time:
        h, m = time.groups()
        h = int(h) if 0<=int(h)<24 else 0
        m = int(m) if 0<=int(m)<60 else 0
        stamp = h*60 + m
        return stamp
