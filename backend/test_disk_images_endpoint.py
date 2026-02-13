#!/usr/bin/env python3
"""
Test script to verify disk images endpoint
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forensic_backend.settings')
django.setup()

from forensic_api.disk_images import get_available_disk_images

print("Testing disk images detection...")
print("=" * 60)

images = get_available_disk_images()

print(f"\nFound {len(images)} disk images:\n")

for img in images:
    print(f"Filename: {img['filename']}")
    print(f"  Size: {img['size_formatted']}")
    print(f"  Extension: {img['extension']}")
    print(f"  Path: {img['path']}")
    print(f"  Modified: {img['modified']}")
    print()

if len(images) == 0:
    print("❌ No disk images found!")
    print("   Make sure disk images are in: forensic_ir_app/data/samples/")
else:
    print(f"✅ Successfully found {len(images)} disk images!")

print("\nTesting API endpoint...")
print("-" * 60)

from forensic_api.views import DiskImagesView
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()
request = factory.get('/api/disk-images/')
view = DiskImagesView.as_view()
response = view(request)

print(f"Status Code: {response.status_code}")
print(f"Response Data: {response.data}")

if response.status_code == 200:
    print(f"\n✅ API endpoint working! Found {response.data['count']} images")
else:
    print(f"\n❌ API endpoint failed with status {response.status_code}")
