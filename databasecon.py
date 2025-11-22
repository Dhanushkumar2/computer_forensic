from psycopg2 import connect
from pymongo import MongoClient
from neo4j import GraphDatabase
from pymilvus import connections
from pymilvus import connections, utility

# PostgreSQL
pg_conn = connect(
    dbname="forensics",
    user="dhanush",
    password="dkarcher",
    host="localhost",
    port=5432
)
print("PostgreSQL connected")

# MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["forensics"]
print("MongoDB connected")

# Neo4j
# neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
# print("Neo4j connected")

# Milvus

# Connect to Milvus standalone
connections.connect(alias="default", host="127.0.0.1", port="19530")

# Verify
print("Connected to Milvus")

# Check all existing collections
print("Existing collections:", utility.list_collections())
