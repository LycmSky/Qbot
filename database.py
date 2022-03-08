import pymongo, json

with open("./config.json",'r') as load_f:
    datainfo = json.load(load_f)

# 配置数据库地址
host = datainfo["database"]["host"]
port = datainfo["database"]["port"]

def databaseInit(collection):
    mongo_client = pymongo.MongoClient(host=host, port=port)
    return mongo_client.Qbot[collection]