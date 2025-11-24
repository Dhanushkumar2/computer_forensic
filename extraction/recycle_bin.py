#!/usr/bin/env python3
"""
recycle_bin.py
Recycle Bin forensics module for parsing INFO2 files, recovering deleted files,
and extracting deletion timestamps
"""

import os
import struct
from datetime import datetime
import tempfile


class RecycleBinArtifacts:
    def __init__(self, fs):
        self.fs = fs
        
    def read_file_bytes(self, path):
        """Read file bytes from filesystem"""
        try:
            fobj = self.fs.open(path)
            size = fobj.info.meta.size
            return fobj.read_random(0, size)
        except Exception:
            return None
    
    def list_directory_entries(self, path):
        """List directory entries"""
        try:
            directory = self.fs.open_dir(path)
            entries = []
            for entry in directory:
                try:
                    name = entry.info.name.name.decode(errors="ignore")
                    if name not in [".", ".."]:
                        entries.append({
                            "name": name,
                            "path": os.path.join(path, name),
                            "size": entry.info.meta.size if entry.info.meta else 0,
                            "type": "file" if entry.info.meta and entry.info.meta.type == 1 else "directory"
                        })
                except Exception:
                    continue
            return entries
        except Exception:
            return []

    def parse_info2_file(self, info2_path):
        """Parse Windows XP/2000 INFO2 file format"""
        raw_data = self.read_file_bytes(info2_path)
        if not raw_data:
            return []
            
        deleted_files = []
        
        try:
            # INFO2 file header
            if len(raw_data) < 20:
                return []
                
            # Check for INFO2 signature
            header = raw_data[:20]
            version = struct.unpack('<I', header[0:4])[0]
            
            # Skip header, start parsing records
            offset = 20
            record_size = 800  # Standard INFO2 record size
            
            while offset + record_size <= len(raw_data):
                try:
                    record = raw_data[offset:offset + record_size]
                    
                    # Parse record structure
                    original_filename_unicode = record[0:520]  # Unicode filename (260 chars * 2 bytes)
                    record_number = struct.unpack('<I', record[520:524])[0]
                    drive_number = struct.unpack('<I', record[524:528])[0]
                    deletion_time = struct.unpack('<Q', record[528:536])[0]  # FILETIME
                    file_size = struct.unpack('<I', record[536:540])[0]
                    original_filename_ansi = record[540:800]  # ANSI filename
                    
                    # Extract Unicode filename
                    try:
                        filename_unicode = original_filename_unicode.decode('utf-16le').rstrip('\x00')
                    except:
                        filename_unicode = ""
                    
                    # Extract ANSI filename as fallback
                    try:
                        filename_ansi = original_filename_ansi.decode('ascii', errors='ignore').rstrip('\x00')
                    except:
                        filename_ansi = ""
                    
                    # Use Unicode filename if available, otherwise ANSI
                    filename = filename_unicode if filename_unicode else filename_ansi
                    
                    # Convert FILETIME to datetime
                    if deletion_time > 0:
                        try:
                            deletion_dt = datetime.fromtimestamp((deletion_time - 116444736000000000) / 10000000)
                        except:
                            deletion_dt = None
                    else:
                        deletion_dt = None
                    
                    # Generate recycle bin filename
                    drive_letter = chr(ord('A') + drive_number) if drive_number < 26 else 'Unknown'
                    recycle_filename = f"D{drive_letter}{record_number}"
                    
                    deleted_files.append({
                        "original_filename": filename,
                        "recycle_filename": recycle_filename,
                        "deletion_time": deletion_dt.isoformat() if deletion_dt else None,
                        "file_size": file_size,
                        "drive_number": drive_number,
                        "drive_letter": drive_letter,
                        "record_number": record_number
                    })
                    
                except Exception as e:
                    print(f"Error parsing INFO2 record at offset {offset}: {e}")
                
                offset += record_size
                
        except Exception as e:
            print(f"Error parsing INFO2 file: {e}")
            
        return deleted_files

    def parse_recycle_bin_vista_plus(self, recycle_path):
        """Parse Windows Vista+ recycle bin format ($I and $R files)"""
        deleted_files = []
        
        # List all files in recycle bin directory
        entries = self.list_directory_entries(recycle_path)
        
        # Group $I and $R files by their identifier
        file_pairs = {}
        
        for entry in entries:
            filename = entry["name"]
            
            if filename.startswith("$I"):
                # Info file
                identifier = filename[2:]  # Remove $I prefix
                if identifier not in file_pairs:
                    file_pairs[identifier] = {}
                file_pairs[identifier]["info_file"] = entry
                
            elif filename.startswith("$R"):
                # Data file
                identifier = filename[2:]  # Remove $R prefix
                if identifier not in file_pairs:
                    file_pairs[identifier] = {}
                file_pairs[identifier]["data_file"] = entry
        
        # Parse each file pair
        for identifier, files in file_pairs.items():
            if "info_file" in files:
                info_data = self.read_file_bytes(files["info_file"]["path"])
                if info_data:
                    deleted_file_info = self._parse_vista_info_file(info_data, identifier)
                    if deleted_file_info:
                        # Add data file info if available
                        if "data_file" in files:
                            deleted_file_info["data_file_size"] = files["data_file"]["size"]
                            deleted_file_info["data_file_path"] = files["data_file"]["path"]
                        
                        deleted_files.append(deleted_file_info)
        
        return deleted_files

    def _parse_vista_info_file(self, info_data, identifier):
        """Parse Windows Vista+ $I info file"""
        try:
            if len(info_data) < 24:
                return None
            
            # Parse header
            header_size = struct.unpack('<Q', info_data[0:8])[0]
            deletion_time = struct.unpack('<Q', info_data[8:16])[0]
            file_size = struct.unpack('<Q', info_data[16:24])[0]
            
            # Parse filename (Unicode, null-terminated)
            filename_data = info_data[24:]
            try:
                filename = filename_data.decode('utf-16le').rstrip('\x00')
            except:
                filename = "Unknown"
            
            # Convert FILETIME to datetime
            if deletion_time > 0:
                try:
                    deletion_dt = datetime.fromtimestamp((deletion_time - 116444736000000000) / 10000000)
                except:
                    deletion_dt = None
            else:
                deletion_dt = None
            
            return {
                "original_filename": filename,
                "recycle_filename": f"$R{identifier}",
                "info_filename": f"$I{identifier}",
                "deletion_time": deletion_dt.isoformat() if deletion_dt else None,
                "file_size": file_size,
                "header_size": header_size,
                "identifier": identifier
            }
            
        except Exception as e:
            print(f"Error parsing Vista+ info file: {e}")
            return None

    def recover_deleted_file_content(self, data_file_path, output_path=None):
        """Recover content of deleted file"""
        content = self.read_file_bytes(data_file_path)
        
        if content and output_path:
            try:
                with open(output_path, 'wb') as f:
                    f.write(content)
                return True
            except Exception as e:
                print(f"Error writing recovered file: {e}")
                return False
        
        return content

    def analyze_recycle_bin_locations(self):
        """Find and analyze all recycle bin locations"""
        recycle_locations = []
        
        # Common recycle bin paths
        common_paths = [
            "/RECYCLER",
            "/Recycler", 
            "/$Recycle.Bin",
            "/RECYCLED"
        ]
        
        for path in common_paths:
            entries = self.list_directory_entries(path)
            if entries:
                recycle_locations.append({
                    "path": path,
                    "type": "vista_plus" if "$Recycle.Bin" in path else "xp_2000",
                    "entries": entries
                })
        
        return recycle_locations

    def extract_all_recycle_bin_artifacts(self):
        """Extract all recycle bin artifacts"""
        artifacts = {
            "locations": [],
            "deleted_files": [],
            "summary": {
                "total_deleted_files": 0,
                "total_size": 0,
                "date_range": {"earliest": None, "latest": None}
            }
        }
        
        # Find recycle bin locations
        locations = self.analyze_recycle_bin_locations()
        artifacts["locations"] = locations
        
        total_size = 0
        deletion_times = []
        
        for location in locations:
            location_path = location["path"]
            location_type = location["type"]
            
            if location_type == "xp_2000":
                # Look for INFO2 files
                for entry in location["entries"]:
                    if entry["name"].upper() == "INFO2":
                        info2_files = self.parse_info2_file(entry["path"])
                        artifacts["deleted_files"].extend(info2_files)
                        
                        # Update statistics
                        for file_info in info2_files:
                            total_size += file_info.get("file_size", 0)
                            if file_info.get("deletion_time"):
                                deletion_times.append(file_info["deletion_time"])
            
            elif location_type == "vista_plus":
                # Look for user-specific recycle bins
                for entry in location["entries"]:
                    if entry["type"] == "directory":
                        user_recycle_path = entry["path"]
                        vista_files = self.parse_recycle_bin_vista_plus(user_recycle_path)
                        
                        # Add user context
                        for file_info in vista_files:
                            file_info["user_sid"] = entry["name"]
                        
                        artifacts["deleted_files"].extend(vista_files)
                        
                        # Update statistics
                        for file_info in vista_files:
                            total_size += file_info.get("file_size", 0)
                            if file_info.get("deletion_time"):
                                deletion_times.append(file_info["deletion_time"])
        
        # Update summary statistics
        artifacts["summary"]["total_deleted_files"] = len(artifacts["deleted_files"])
        artifacts["summary"]["total_size"] = total_size
        
        if deletion_times:
            deletion_times.sort()
            artifacts["summary"]["date_range"]["earliest"] = deletion_times[0]
            artifacts["summary"]["date_range"]["latest"] = deletion_times[-1]
        
        return artifacts

    def search_deleted_files_by_extension(self, file_extension):
        """Search for deleted files by extension"""
        all_artifacts = self.extract_all_recycle_bin_artifacts()
        
        matching_files = []
        for file_info in all_artifacts["deleted_files"]:
            filename = file_info.get("original_filename", "")
            if filename.lower().endswith(file_extension.lower()):
                matching_files.append(file_info)
        
        return matching_files

    def search_deleted_files_by_date_range(self, start_date, end_date):
        """Search for deleted files within date range"""
        all_artifacts = self.extract_all_recycle_bin_artifacts()
        
        matching_files = []
        for file_info in all_artifacts["deleted_files"]:
            deletion_time = file_info.get("deletion_time")
            if deletion_time:
                if start_date <= deletion_time <= end_date:
                    matching_files.append(file_info)
        
        return matching_files