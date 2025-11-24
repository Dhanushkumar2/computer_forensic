#!/usr/bin/env python3
"""
Test database connections (MongoDB and PostgreSQL)
"""

import sys
from pymongo import MongoClient
import psycopg2


def test_mongodb():
    """Test MongoDB connection"""
    
    print("=" * 70)
    print("  Testing MongoDB Connection")
    print("=" * 70)
    
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.server_info()
        
        print("\n✅ MongoDB is accessible")
        
        # List databases
        dbs = client.list_database_names()
        print(f"   Databases: {', '.join(dbs)}")
        
        # Check forensics database
        if 'forensics' in dbs:
            db = client['forensics']
            collections = db.list_collection_names()
            print(f"   Forensics collections: {len(collections)}")
            if collections:
                print(f"   - {', '.join(collections[:5])}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB connection failed: {e}")
        print("   Start MongoDB: sudo systemctl start mongod")
        return False


def test_postgresql():
    """Test PostgreSQL connection"""
    
    print("\n" + "=" * 70)
    print("  Testing PostgreSQL Connection")
    print("=" * 70)
    
    try:
        conn = psycopg2.connect(
            dbname="forensics",
            user="dhanush",
            password="dkarcher",
            host="localhost",
            port=5432
        )
        
        print("\n✅ PostgreSQL is accessible")
        
        # Get version
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"   Version: {version[0].split(',')[0]}")
        
        # Check tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cur.fetchall()
        if tables:
            print(f"   Tables: {len(tables)}")
            for table in tables[:5]:
                print(f"   - {table[0]}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ PostgreSQL connection failed: {e}")
        print("   Start PostgreSQL: sudo systemctl start postgresql")
        return False


if __name__ == "__main__":
    mongodb_ok = test_mongodb()
    postgresql_ok = test_postgresql()
    
    print("\n" + "=" * 70)
    print("  Database Connection Summary")
    print("=" * 70)
    print(f"  MongoDB: {'✅ PASS' if mongodb_ok else '❌ FAIL'}")
    print(f"  PostgreSQL: {'✅ PASS' if postgresql_ok else '❌ FAIL'}")
    print("=" * 70)
    
    sys.exit(0 if (mongodb_ok and postgresql_ok) else 1)