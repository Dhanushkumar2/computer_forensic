#!/usr/bin/env python3
"""
Manual extraction script to extract data from sample disk images
and store in MongoDB database
"""
import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.dirname(__file__))

from extraction.forensic_extractor import ForensicExtractor
from database.mongodb_storage import ForensicMongoStorage
import json

def extract_and_store(image_path, case_id):
    """Extract artifacts from disk image and store in MongoDB"""
    
    print(f"\n{'='*60}")
    print(f"Processing: {image_path}")
    print(f"Case ID: {case_id}")
    print(f"{'='*60}\n")
    
    # Initialize extractor
    extractor = ForensicExtractor(image_path)
    
    try:
        # Extract all artifacts
        print("Starting extraction...")
        artifacts = extractor.extract_all_artifacts()
        
        if not artifacts:
            print("❌ Extraction failed!")
            return False
        
        # Print summary
        print("\n=== EXTRACTION SUMMARY ===")
        summary = artifacts.get("summary", {})
        for key, value in summary.items():
            if key != "extraction_timestamp":
                print(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Store in MongoDB
        print("\n📦 Storing artifacts in MongoDB...")
        storage = ForensicMongoStorage(config_path="forensic_ir_app/config/db_config.yaml")
        
        # Store browser artifacts
        browser_count = storage.store_browser_artifacts(case_id, artifacts.get("browser_artifacts", {}))
        print(f"  ✓ Browser artifacts: {browser_count}")
        
        # Store USB devices
        usb_count = storage.store_usb_devices(case_id, artifacts.get("registry_artifacts", {}).get("usb_history", []))
        print(f"  ✓ USB devices: {usb_count}")
        
        # Store user activity
        activity_count = storage.store_user_activity(case_id, artifacts.get("registry_artifacts", {}).get("userassist", []))
        print(f"  ✓ User activity: {activity_count}")
        
        # Store installed programs
        programs_count = storage.store_installed_programs(case_id, artifacts.get("registry_artifacts", {}).get("installed_programs", []))
        print(f"  ✓ Installed programs: {programs_count}")
        
        # Store other registry artifacts
        registry_count = storage.store_registry_artifacts(case_id, artifacts.get("registry_artifacts", {}))
        print(f"  ✓ Registry artifacts: {registry_count}")
        
        # Store event logs
        events_count = storage.store_event_logs(case_id, artifacts.get("event_log_artifacts", {}))
        print(f"  ✓ Event logs: {events_count}")
        
        # Store filesystem artifacts
        fs_count = storage.store_filesystem_artifacts(case_id, artifacts.get("filesystem_artifacts", {}))
        print(f"  ✓ Filesystem artifacts: {fs_count}")
        
        # Store recycle bin artifacts
        recycle_count = storage.store_recycle_bin_artifacts(case_id, artifacts.get("recycle_bin_artifacts", {}))
        print(f"  ✓ Recycle bin artifacts: {recycle_count}")
        
        # Create timeline
        timeline_count = storage.create_timeline_events(case_id)
        print(f"  ✓ Timeline events: {timeline_count}")
        
        storage.close()
        print("✅ Successfully stored all artifacts in MongoDB!")
        
        # Also save to JSON file for backup
        output_file = f"data/extracted/{case_id}_artifacts.json"
        os.makedirs("data/extracted", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(artifacts, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"📄 Backup JSON saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        extractor.close()


def main():
    """Main function to process all sample images"""
    
    # Sample images directory
    samples_dir = Path("data/samples")
    
    if not samples_dir.exists():
        print(f"❌ Samples directory not found: {samples_dir}")
        return
    
    # Find all disk images
    image_extensions = ['.E01', '.E02', '.dd', '.raw', '.img', '.001']
    disk_images = []
    
    for ext in image_extensions:
        disk_images.extend(samples_dir.glob(f"*{ext}"))
        disk_images.extend(samples_dir.glob(f"*{ext.lower()}"))
    
    # Remove duplicates
    disk_images = list(set(disk_images))
    
    if not disk_images:
        print("❌ No disk images found in data/samples/")
        print(f"   Supported formats: {', '.join(image_extensions)}")
        return
    
    print(f"\n🔍 Found {len(disk_images)} disk image(s):")
    for i, img in enumerate(disk_images, 1):
        print(f"  {i}. {img.name}")
    
    # Process each image
    for i, image_path in enumerate(disk_images, 1):
        case_id = f"CASE_{image_path.stem.upper().replace(' ', '_').replace('.', '_')}"
        
        print(f"\n\n{'#'*60}")
        print(f"# Processing Image {i}/{len(disk_images)}")
        print(f"{'#'*60}")
        
        success = extract_and_store(str(image_path), case_id)
        
        if success:
            print(f"\n✅ Successfully processed: {image_path.name}")
        else:
            print(f"\n❌ Failed to process: {image_path.name}")
    
    print(f"\n\n{'='*60}")
    print("🎉 All disk images processed!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║     FORENSIC IR - MANUAL SAMPLE DATA EXTRACTION              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check if specific image is provided
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        case_id = sys.argv[2] if len(sys.argv) > 2 else f"CASE_{Path(image_path).stem.upper()}"
        
        if not os.path.exists(image_path):
            print(f"❌ Image file not found: {image_path}")
            sys.exit(1)
        
        extract_and_store(image_path, case_id)
    else:
        # Process all images in samples directory
        main()
