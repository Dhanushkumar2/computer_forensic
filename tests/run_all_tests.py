#!/usr/bin/env python3
"""
Run all tests for the Forensic Investigation System
"""

import os
import sys
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def run_test(test_file, description):
    """Run a test file and return success status"""
    
    print_header(description)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            timeout=900  # 15 minutes
        )
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"\n❌ Test timed out: {test_file}")
        return False
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


def main():
    """Run all tests"""
    
    print_header("🧪 Forensic Investigation System - Complete Test Suite")
    print("This will run all tests to verify system functionality")
    
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    results = {}
    
    # Test 1: Database Connections
    results['connections'] = run_test(
        os.path.join(tests_dir, 'test_database_connections.py'),
        "Test 1: Database Connections"
    )
    
    # Test 2: Forensic Extraction
    results['extraction'] = run_test(
        os.path.join(tests_dir, 'test_extraction.py'),
        "Test 2: Forensic Artifact Extraction"
    )
    
    # Test 3: MongoDB Storage and Retrieval
    if results['extraction']:
        results['mongodb'] = run_test(
            os.path.join(tests_dir, 'test_mongodb.py'),
            "Test 3: MongoDB Storage and Retrieval"
        )
    else:
        print_header("Test 3: MongoDB Storage and Retrieval")
        print("\n⚠️  Skipped - extraction test failed")
        results['mongodb'] = False
    
    # Print summary
    print_header("📊 Test Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"  {status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n  Tests passed: {passed}/{total}")
    
    if passed == total:
        print_header("🎉 All Tests Passed!")
        print("\n✅ Your forensic investigation system is fully functional!")
        print("\nNext steps:")
        print("  1. View results: python scripts/show_results.py")
        print("  2. Run analysis: python scripts/analyze_case.py")
        print("  3. Setup Django: cd backend && python setup_django.py")
    else:
        print_header("⚠️  Some Tests Failed")
        print("\nPlease check the error messages above and:")
        print("  1. Ensure MongoDB is running: sudo systemctl start mongod")
        print("  2. Ensure PostgreSQL is running: sudo systemctl start postgresql")
        print("  3. Check that the E01 image file exists")
        print("  4. Review logs for detailed error information")
    
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)