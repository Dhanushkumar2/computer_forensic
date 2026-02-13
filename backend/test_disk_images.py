#!/usr/bin/env python3
"""
Test script to verify disk image detection
"""
import sys
import os

# Add the forensic_api to path
sys.path.insert(0, os.path.dirname(__file__))

from forensic_api.disk_images import get_available_disk_images

print("Testing disk image detection...")
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
    print("No disk images found!")
    print("Make sure disk images are in: forensic_ir_app/data/samples/")
    print("Supported formats: .E01, .E02, .dd, .raw, .img, .001, .aff, .afd")
