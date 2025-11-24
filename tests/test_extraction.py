#!/usr/bin/env python3
"""
Test forensic artifact extraction
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extraction.forensic_extractor import ForensicExtractor


def test_extraction():
    """Test artifact extraction from E01 image"""
    
    print("=" * 70)
    print("  Testing Forensic Artifact Extraction")
    print("=" * 70)
    
    # Image path
    image_path = "/home/dhanush/myvenv/forensic_ir_app/data/samples/nps-2008-jean.E01"
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False
    
    print(f"\n✓ Image found: {image_path}")
    
    # Initialize extractor
    print("\n1. Initializing extractor...")
    extractor = ForensicExtractor(image_path)
    
    # Extract artifacts
    print("2. Extracting artifacts (this may take 5-10 minutes)...")
    output_file = "test_artifacts.json"
    
    try:
        artifacts = extractor.extract_all_artifacts(output_file)
        
        if artifacts:
            print(f"\n✅ Extraction successful!")
            print(f"   Output: {output_file}")
            
            # Show summary
            summary = artifacts.get('summary', {})
            print("\n📊 Extraction Summary:")
            for key, value in summary.items():
                if key != 'extraction_timestamp':
                    print(f"   {key.replace('_', ' ').title()}: {value}")
            
            return True
        else:
            print("❌ Extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return False
    finally:
        extractor.close()


if __name__ == "__main__":
    success = test_extraction()
    sys.exit(0 if success else 1)