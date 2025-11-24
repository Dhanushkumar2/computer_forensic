#!/usr/bin/env python3
"""
Test MongoDB storage and retrieval
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongodb_storage import ForensicMongoStorage
from database.mongodb_retrieval import ForensicMongoRetrieval


def test_mongodb_connection():
    """Test MongoDB connection"""
    
    print("=" * 70)
    print("  Testing MongoDB Connection")
    print("=" * 70)
    
    try:
        retrieval = ForensicMongoRetrieval()
        cases = retrieval.get_all_cases()
        
        print(f"\n✅ MongoDB connected successfully")
        print(f"   Found {len(cases)} case(s)")
        
        retrieval.close()
        return True
        
    except Exception as e:
        print(f"\n❌ MongoDB connection failed: {e}")
        print("   Make sure MongoDB is running: sudo systemctl start mongod")
        return False


def test_mongodb_storage(json_file):
    """Test storing artifacts in MongoDB"""
    
    print("\n" + "=" * 70)
    print("  Testing MongoDB Storage")
    print("=" * 70)
    
    if not os.path.exists(json_file):
        print(f"\n❌ Artifacts file not found: {json_file}")
        return False
    
    try:
        storage = ForensicMongoStorage()
        case_id = storage.store_all_artifacts(json_file)
        
        print(f"\n✅ Artifacts stored successfully")
        print(f"   Case ID: {case_id}")
        
        storage.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Storage failed: {e}")
        return False


def test_mongodb_retrieval(case_id):
    """Test retrieving artifacts from MongoDB"""
    
    print("\n" + "=" * 70)
    print("  Testing MongoDB Retrieval")
    print("=" * 70)
    
    try:
        retrieval = ForensicMongoRetrieval()
        
        # Test case summary
        print("\n1. Testing case summary...")
        summary = retrieval.get_case_summary(case_id)
        if summary:
            print("   ✓ Case summary retrieved")
            counts = summary.get('counts', {})
            print(f"   - Browser history: {counts.get('browser_history', 0)}")
            print(f"   - USB devices: {counts.get('usb_devices', 0)}")
            print(f"   - User activity: {counts.get('user_activity', 0)}")
        
        # Test USB devices
        print("\n2. Testing USB device retrieval...")
        usb_devices = retrieval.get_usb_devices(case_id)
        print(f"   ✓ Retrieved {len(usb_devices)} USB devices")
        
        # Test user activity
        print("\n3. Testing user activity retrieval...")
        activity = retrieval.get_user_activity(case_id, limit=10)
        print(f"   ✓ Retrieved {len(activity)} activity records")
        
        # Test timeline
        print("\n4. Testing timeline retrieval...")
        timeline = retrieval.get_timeline(case_id, limit=10)
        print(f"   ✓ Retrieved {len(timeline)} timeline events")
        
        # Test search
        print("\n5. Testing artifact search...")
        results = retrieval.search_artifacts(case_id, "usb")
        total = sum(len(v) for v in results.values())
        print(f"   ✓ Search found {total} results")
        
        print("\n✅ All retrieval tests passed")
        
        retrieval.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Retrieval test failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection
    if not test_mongodb_connection():
        sys.exit(1)
    
    # Test storage
    json_file = "test_artifacts.json"
    if os.path.exists(json_file):
        if not test_mongodb_storage(json_file):
            sys.exit(1)
        
        # Get case ID from stored data
        import json
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Extract case_id or use default
        case_id = data.get('extraction_info', {}).get('case_id', 'CASE_20251124_030926')
        
        # Test retrieval
        if not test_mongodb_retrieval(case_id):
            sys.exit(1)
    else:
        print(f"\n⚠️  Skipping storage test - no artifacts file found")
        print(f"   Run: python tests/test_extraction.py")
    
    print("\n" + "=" * 70)
    print("  ✅ All MongoDB tests passed")
    print("=" * 70)
    
    sys.exit(0)