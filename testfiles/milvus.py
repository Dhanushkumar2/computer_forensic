from pymilvus import connections, utility

connections.connect(alias="default", host="127.0.0.1", port="19530")

# Check if collection exists
print(utility.has_collection("forensic_vectors"))

# List all collections
print(utility.list_collections())

from pymilvus import Collection
c = Collection("forensic_vectors")
print(c.schema)

