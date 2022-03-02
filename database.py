import pymongo

# 配置数据库地址
host = 'localhost'
port = 27017

def databaseInit(collection):
    mongo_client = pymongo.MongoClient(host=host, port=port)
    return mongo_client.Qbot[collection]