import pymongo
import sys
# connnecto to the db on standard port
try:
    connection = pymongo.MongoClient("mongodb://localhost")
    db = connection.syscat                 # attach to db
    collection = db.datos         # specify the colllection

except Exception as e:
    print ("Error trying to connect to the database:" + e)
