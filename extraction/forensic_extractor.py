#!/usr/bin/env python3
"""
forensic_extractor.py
Main forensic artifact extraction orchestrator that coordinates all extraction modules
"""

import json
import os
from datetime import datetime
import pyewf
import pytsk3

from .browser_artifacts import BrowserArtifacts
from .registry_artifacts import RegistryArtifacts
from .recycle_bin import RecycleBinArtifacts
from .event_logs import EventLogArtifacts
from .filesystem_artifacts import FileSystemArtifacts


class EWFImgInfo(pytsk3.Img_Info):
    """Wrapper class for EWF images to work with pytsk3"""
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(EWFImgInfo, self).__init__(url="")

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()


class ForensicExtractor:
    def __init__(self, image_path):
        self.image_path = image_path
        self.ewf_handle = None
        self.img = None
        self.fs = None
        self.ntfs_offset = None
        
        # Initialize extraction modules
        self.browser_extractor = None
        self.registry_extractor = None
        self.recycle_bin_extractor = None
        self.event_log_extractor = None
        self.filesystem_extractor = None
        
    def open_image(self):
        """Open the forensic image and mount the filesystem"""
        try:
            # Open EWF image
            files = pyewf.glob(self.image_path)
            if not files:
                files = [self.image_path]
            
            self.ewf_handle = pyewf.handle()
            self.ewf_handle.open(files)
            
            # Create pytsk3 image wrapper
            self.img = EWFImgInfo(self.ewf_handle)
            
            # Find NTFS partition
            self._find_ntfs_partition()
            
            # Mount filesystem
            if self.ntfs_offset is not None:
                self.fs = pytsk3.FS_Info(self.img, offset=self.ntfs_offset)
                
                # Initialize extraction modules
                self.browser_extractor = BrowserArtifacts(self.fs)
                self.registry_extractor = RegistryArtifacts(self.fs)
                self.recycle_bin_extractor = RecycleBinArtifacts(self.fs)
                self.event_log_extractor = EventLogArtifacts(self.fs)
                self.filesystem_extractor = FileSystemArtifacts(self.fs)
                
                return True
            else:
                print("No NTFS partition found")
                return False
                
        except Exception as e:
            print(f"Error opening image: {e}")
            return False
    
    def _find_ntfs_partition(self):
        """Find NTFS partition in the image"""
        try:
            volume = pytsk3.Volume_Info(self.img)
            
            for part in volume:
                desc = part.desc
                if isinstance(desc, bytes):
                    desc = desc.decode(errors="ignore")
                
                if "NTFS" in desc.upper() or "0x07" in desc:
                    self.ntfs_offset = part.start * 512
                    print(f"Found NTFS partition at offset: {self.ntfs_offset}")
                    break
                    
        except Exception as e:
            print(f"Error finding NTFS partition: {e}")
    
    def discover_user_profiles(self):
        """Discover user profiles in the system"""
        profiles = []
        
        # Common user profile locations
        profile_paths = [
            "/Documents and Settings",
            "/Users"
        ]
        
        for base_path in profile_paths:
            try:
                directory = self.fs.open_dir(base_path)
                for entry in directory:
                    try:
                        name = entry.info.name.name.decode(errors="ignore")
                        if name not in [".", "..", "All Users", "Default User", "Public", "Default"]:
                            profiles.append(os.path.join(base_path, name))
                    except Exception:
                        continue
            except Exception:
                continue
        
        return profiles
    
    def extract_browser_artifacts(self, user_profiles):
        """Extract all browser artifacts"""
        if not self.browser_extractor:
            return {}
        
        print("Extracting browser artifacts...")
        return self.browser_extractor.extract_all_browser_artifacts(user_profiles)
    
    def extract_registry_artifacts(self):
        """Extract all registry artifacts"""
        if not self.registry_extractor:
            return {}
        
        print("Extracting registry artifacts...")
        
        # Registry hive paths
        system_hive = "/Windows/System32/config/SYSTEM"
        software_hive = "/Windows/System32/config/SOFTWARE"
        
        # Find NTUSER.DAT files
        user_profiles = self.discover_user_profiles()
        ntuser_paths = []
        for profile in user_profiles:
            ntuser_path = os.path.join(profile, "NTUSER.DAT")
            ntuser_paths.append(ntuser_path)
        
        return self.registry_extractor.extract_all_registry_artifacts(
            system_hive, software_hive, ntuser_paths
        )
    
    def extract_recycle_bin_artifacts(self):
        """Extract recycle bin artifacts"""
        if not self.recycle_bin_extractor:
            return {}
        
        print("Extracting recycle bin artifacts...")
        return self.recycle_bin_extractor.extract_all_recycle_bin_artifacts()
    
    def extract_event_log_artifacts(self):
        """Extract event log artifacts"""
        if not self.event_log_extractor:
            return {}
        
        print("Extracting event log artifacts...")
        return self.event_log_extractor.extract_all_event_log_artifacts()
    
    def extract_filesystem_artifacts(self):
        """Extract filesystem artifacts"""
        if not self.filesystem_extractor:
            return {}
        
        print("Extracting filesystem artifacts...")
        return self.filesystem_extractor.extract_all_filesystem_artifacts()
    
    def extract_all_artifacts(self, output_file=None):
        """Extract all forensic artifacts"""
        if not self.open_image():
            return None
        
        print(f"Starting comprehensive forensic extraction from: {self.image_path}")
        
        # Discover user profiles
        user_profiles = self.discover_user_profiles()
        print(f"Found {len(user_profiles)} user profiles: {user_profiles}")
        
        # Extract all artifact types
        all_artifacts = {
            "extraction_info": {
                "image_path": self.image_path,
                "extraction_time": datetime.now().isoformat(),
                "ntfs_offset": self.ntfs_offset,
                "user_profiles": user_profiles
            },
            "browser_artifacts": self.extract_browser_artifacts(user_profiles),
            "registry_artifacts": self.extract_registry_artifacts(),
            "recycle_bin_artifacts": self.extract_recycle_bin_artifacts(),
            "event_log_artifacts": self.extract_event_log_artifacts(),
            "filesystem_artifacts": self.extract_filesystem_artifacts()
        }
        
        # Generate summary statistics
        summary = self._generate_summary(all_artifacts)
        all_artifacts["summary"] = summary
        
        # Save to file if specified
        if output_file:
            self._save_artifacts(all_artifacts, output_file)
        
        print("Forensic extraction completed!")
        return all_artifacts
    
    def _generate_summary(self, artifacts):
        """Generate summary statistics"""
        summary = {
            "total_browser_history": 0,
            "total_browser_cookies": 0,
            "total_browser_downloads": 0,
            "total_usb_devices": 0,
            "total_userassist_entries": 0,
            "total_installed_programs": 0,
            "total_run_keys": 0,
            "total_deleted_files": 0,
            "total_event_log_entries": 0,
            "total_prefetch_files": 0,
            "total_link_files": 0,
            "extraction_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Browser artifacts
            browser_artifacts = artifacts.get("browser_artifacts", {})
            for browser in ["firefox", "chrome_edge", "internet_explorer"]:
                if browser in browser_artifacts:
                    summary["total_browser_history"] += len(browser_artifacts[browser].get("history", []))
                    summary["total_browser_cookies"] += len(browser_artifacts[browser].get("cookies", []))
                    if "downloads" in browser_artifacts[browser]:
                        summary["total_browser_downloads"] += len(browser_artifacts[browser]["downloads"])
            
            # Registry artifacts
            registry_artifacts = artifacts.get("registry_artifacts", {})
            summary["total_usb_devices"] = len(registry_artifacts.get("usb_history", []))
            summary["total_userassist_entries"] = len(registry_artifacts.get("userassist", []))
            summary["total_installed_programs"] = len(registry_artifacts.get("installed_programs", []))
            summary["total_run_keys"] = len(registry_artifacts.get("run_keys", []))
            
            # Recycle bin artifacts
            recycle_artifacts = artifacts.get("recycle_bin_artifacts", {})
            summary["total_deleted_files"] = len(recycle_artifacts.get("deleted_files", []))
            
            # Event log artifacts
            event_artifacts = artifacts.get("event_log_artifacts", {})
            summary["total_event_log_entries"] = len(event_artifacts.get("all_events", []))
            
            # Filesystem artifacts
            fs_artifacts = artifacts.get("filesystem_artifacts", {})
            summary["total_prefetch_files"] = len(fs_artifacts.get("prefetch_files", []))
            summary["total_link_files"] = len(fs_artifacts.get("link_files", []))
            
        except Exception as e:
            print(f"Error generating summary: {e}")
        
        return summary
    
    def _save_artifacts(self, artifacts, output_file):
        """Save artifacts to JSON file"""
        try:
            def json_serializer(obj):
                """Custom JSON serializer for datetime and other objects"""
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                elif isinstance(obj, bytes):
                    return obj.hex()
                else:
                    return str(obj)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(artifacts, f, indent=2, default=json_serializer, ensure_ascii=False)
            
            print(f"Artifacts saved to: {output_file}")
            
        except Exception as e:
            print(f"Error saving artifacts: {e}")
    
    def search_artifacts(self, search_term, artifact_types=None):
        """Search across all extracted artifacts"""
        if artifact_types is None:
            artifact_types = ["browser", "registry", "recycle_bin", "event_log", "filesystem"]
        
        results = {
            "search_term": search_term,
            "matches": []
        }
        
        # This would implement cross-artifact searching
        # For now, return placeholder
        results["note"] = "Cross-artifact search functionality would be implemented here"
        
        return results
    
    def generate_timeline(self):
        """Generate timeline of all activities"""
        timeline_events = []
        
        # This would collect all timestamped events from all artifacts
        # and create a unified timeline
        
        return {
            "timeline": timeline_events,
            "note": "Timeline generation would aggregate all timestamped events"
        }
    
    def close(self):
        """Clean up resources"""
        try:
            if self.ewf_handle:
                self.ewf_handle.close()
        except Exception as e:
            print(f"Error closing resources: {e}")


# CLI interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python forensic_extractor.py <image_path> [output_file]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "comprehensive_forensic_artifacts.json"
    
    extractor = ForensicExtractor(image_path)
    
    try:
        artifacts = extractor.extract_all_artifacts(output_file)
        
        if artifacts:
            print("\n=== EXTRACTION SUMMARY ===")
            summary = artifacts.get("summary", {})
            for key, value in summary.items():
                if key != "extraction_timestamp":
                    print(f"{key.replace('_', ' ').title()}: {value}")
        
    except KeyboardInterrupt:
        print("\nExtraction interrupted by user")
    except Exception as e:
        print(f"Extraction failed: {e}")
    finally:
        extractor.close()