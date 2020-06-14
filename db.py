# -*- coding: utf-8 -*-

import pymongo

config_uri = "mongodb://user:Ololosha123@ds119024.mlab.com:19024/journals"
client = pymongo.MongoClient(config_uri)

db = client.get_default_database()["users"]
journal = client.get_default_database()["journal"]