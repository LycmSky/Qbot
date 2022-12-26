import json
import pymongo

class Database:
    def __init__(self, name: str) -> None:
        with open("./config.json",'r') as load_f:
            datainfo = json.load(load_f)
        self.filter = {"name": name}
        self.mods = pymongo.MongoClient(host=datainfo["database"]["host"], port=datainfo["database"]["port"]).Qbot['mods']
        self.data = self.mods.find_one(self.filter)

    def init_database(self, data):
        '''初始化数据库'''
        if self.data == None:
            self.mods.insert_one(data)

    def update(self, key: str, data):
        '''更新数据库'''
        self.mods.update_one(self.filter, {"$set": {key: data}})
        self.data = self.mods.find_one(self.filter)
