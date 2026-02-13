#!/usr/bin/env python
"""
Test script for case creation API
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forensic_backend.settings')
django.setup()

from forensic_api.models import ForensicCase
from django.contrib.auth.models import User

def test_case_creation():
    """Test creating a case"""
    print("Testing case creation...")
    
    # Get or create user
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@forensic.local', 'is_staff': True}
    )
    print(f"User: {user.username} (created: {created})")
    
    # Create a test case
    case = ForensicCase.objects.create(
        title="Test Case",
        description="Test case for API",
        priority="high",
        status="pending",
        created_by=user,
        assigned_to=user
    )
    
    print(f"Created case: {case.case_id}")
    print(f"  Title: {case.title}")
    print(f"  Status: {case.status}")
    print(f"  Priority: {case.priority}")
    print(f"  Created by: {case.created_by.username}")
    
    # List all cases
    print("\nAll cases:")
    for c in ForensicCase.objects.all():
        print(f"  - {c.case_id}: {c.title} ({c.status})")
    
    print("\n✅ Test passed!")

if __name__ == '__main__':
    test_case_creation()
