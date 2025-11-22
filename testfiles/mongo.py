from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["forensics"]

# List collections
print(db.list_collection_names())

# Sample document (if any)
print(db.artifacts.find_one())
