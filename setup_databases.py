# setup_databases.py
import psycopg2
from pymongo import MongoClient
from neo4j import GraphDatabase
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility
import yaml


with open("forensic_ir_app/config/db_config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

# PostgreSQL Setup
pg_conn = psycopg2.connect(
    host=cfg["postgres"]["host"],
    port=cfg["postgres"]["port"],
    user=cfg["postgres"]["user"],
    password=cfg["postgres"]["password"],
    dbname=cfg["postgres"]["database"]
)
pg_cur = pg_conn.cursor()

# Create tables
pg_cur.execute("""
CREATE TABLE IF NOT EXISTS artifacts (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255),
    filepath VARCHAR(1024),
    size BIGINT,
    sha256 VARCHAR(64),
    created TIMESTAMP,
    modified TIMESTAMP,
    accessed TIMESTAMP,
    owner VARCHAR(255),
    deleted BOOLEAN,
    file_type VARCHAR(50),
    case_id VARCHAR(100)
);
""")

pg_cur.execute("""
CREATE TABLE IF NOT EXISTS timeline_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    event_type VARCHAR(50),
    description TEXT,
    artifact_id INT REFERENCES artifacts(id),
    case_id VARCHAR(100)
);
""")

pg_conn.commit()
pg_cur.close()
pg_conn.close()
print("PostgreSQL tables created successfully!")


#  MongoDB Setup
mongo_client = MongoClient(cfg["mongodb"]["uri"])
mongo_db = mongo_client[cfg["mongodb"]["database"]]
if "artifacts" not in mongo_db.list_collection_names():
    mongo_db.create_collection("artifacts")
print("MongoDB collection 'artifacts' ready!")
""""
# ----------------------------
# 3 Neo4j Setup
# ----------------------------
neo4j_driver = GraphDatabase.driver(
    "bolt://localhost:7687", auth=(cfg["neo4j"]["user"], cfg["neo4j"]["password"])
)
with neo4j_driver.session() as session:
    # Constraints for uniqueness
    session.run("CREATE CONSTRAINT IF NOT EXISTS ON (f:File) ASSERT f.sha256 IS UNIQUE;")
    session.run("CREATE CONSTRAINT IF NOT EXISTS ON (u:User) ASSERT u.name IS UNIQUE;")
print("Neo4j constraints created successfully!")
"""


# Milvus Setup
connections.connect(alias="default", host="127.0.0.1", port="19530")

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="case_id", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="artifact_id", dtype=DataType.VARCHAR, max_length=100),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768)
]
schema = CollectionSchema(fields, description="Forensic artifact embeddings")

if not utility.has_collection("forensic_vectors"):
    Collection(name="forensic_vectors", schema=schema)

print("Milvus collection 'forensic_vectors' ready!")