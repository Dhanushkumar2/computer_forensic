#!/usr/bin/env python3
"""
filesystem_artifacts.py
File system forensics module for Prefetch parsing, Link files decoding,
Jump lists, and USN Journal analysis
"""

import os
import struct
from datetime import datetime, timedelta
import tempfile


class FileSystemArtifacts:
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
                            "created": entry.info.meta.crtime if entry.info.meta else 0,
                            "modified": entry.info.meta.mtime if entry.info.meta else 0,
                            "accessed": entry.info.meta.atime if entry.info.meta else 0
                        })
                except Exception:
                    continue
            return entries
        except Exception:
            return []

    def parse_prefetch_files(self):
        """Parse Windows Prefetch files"""
        prefetch_path = "/Windows/Prefetch"
        prefetch_files = []
        
        entries = self.list_directory_entries(prefetch_path)
        
        for entry in entries:
            if entry["name"].upper().endswith(".PF"):
                pf_data = self.read_file_bytes(entry["path"])
                if pf_data:
                    parsed_pf = self._parse_prefetch_file(pf_data, entry["name"])
                    if parsed_pf:
                        parsed_pf["file_path"] = entry["path"]
                        parsed_pf["file_size"] = entry["size"]
                        parsed_pf["file_created"] = datetime.fromtimestamp(entry["created"]).isoformat() if entry["created"] else None
                        parsed_pf["file_modified"] = datetime.fromtimestamp(entry["modified"]).isoformat() if entry["modified"] else None
                        prefetch_files.append(parsed_pf)
        
        return prefetch_files

    def _parse_prefetch_file(self, pf_data, filename):
        """Parse individual prefetch file"""
        try:
            if len(pf_data) < 84:
                return None
            
            # Check for prefetch signature
            signature = pf_data[0:4]
            if signature not in [b'SCCA', b'MAM\x04']:
                return None
            
            # Parse header based on version
            version = struct.unpack('<I', pf_data[0:4])[0] if signature == b'SCCA' else struct.unpack('<I', pf_data[4:8])[0]
            
            if version == 0x17:  # Windows XP/2003
                return self._parse_prefetch_v17(pf_data, filename)
            elif version == 0x1A:  # Windows Vista/7
                return self._parse_prefetch_v1A(pf_data, filename)
            elif version == 0x1E:  # Windows 8/8.1
                return self._parse_prefetch_v1E(pf_data, filename)
            elif version == 0x1F:  # Windows 10
                return self._parse_prefetch_v1F(pf_data, filename)
            else:
                print(f"Unknown prefetch version: {hex(version)}")
                return None
                
        except Exception as e:
            print(f"Error parsing prefetch file {filename}: {e}")
            return None

    def _parse_prefetch_v17(self, pf_data, filename):
        """Parse Windows XP/2003 prefetch format"""
        try:
            # XP prefetch header structure
            executable_name_offset = struct.unpack('<I', pf_data[16:20])[0]
            executable_name_length = struct.unpack('<I', pf_data[20:24])[0]
            
            # Extract executable name
            if executable_name_offset < len(pf_data):
                exec_name_data = pf_data[executable_name_offset:executable_name_offset + executable_name_length]
                executable_name = exec_name_data.decode('utf-16le', errors='ignore').rstrip('\x00')
            else:
                executable_name = filename.split('-')[0] if '-' in filename else filename
            
            # Parse run count and last run time
            run_count = struct.unpack('<I', pf_data[144:148])[0]
            last_run_time = struct.unpack('<Q', pf_data[120:128])[0]
            
            # Convert FILETIME to datetime
            if last_run_time > 0:
                last_run_dt = datetime.fromtimestamp((last_run_time - 116444736000000000) / 10000000)
            else:
                last_run_dt = None
            
            return {
                "filename": filename,
                "executable_name": executable_name,
                "run_count": run_count,
                "last_run_time": last_run_dt.isoformat() if last_run_dt else None,
                "version": "XP/2003",
                "prefetch_hash": filename.split('-')[-1].replace('.pf', '') if '-' in filename else ""
            }
            
        except Exception as e:
            print(f"Error parsing XP prefetch: {e}")
            return None

    def _parse_prefetch_v1A(self, pf_data, filename):
        """Parse Windows Vista/7 prefetch format"""
        try:
            # Vista/7 prefetch header
            executable_name_offset = struct.unpack('<I', pf_data[16:20])[0]
            executable_name_length = struct.unpack('<I', pf_data[20:24])[0]
            
            # Extract executable name
            if executable_name_offset < len(pf_data):
                exec_name_data = pf_data[executable_name_offset:executable_name_offset + executable_name_length]
                executable_name = exec_name_data.decode('utf-16le', errors='ignore').rstrip('\x00')
            else:
                executable_name = filename.split('-')[0] if '-' in filename else filename
            
            # Parse run count and last run times (up to 8 timestamps)
            run_count = struct.unpack('<I', pf_data[152:156])[0]
            
            last_run_times = []
            for i in range(8):
                timestamp_offset = 128 + (i * 8)
                if timestamp_offset + 8 <= len(pf_data):
                    timestamp = struct.unpack('<Q', pf_data[timestamp_offset:timestamp_offset + 8])[0]
                    if timestamp > 0:
                        try:
                            dt = datetime.fromtimestamp((timestamp - 116444736000000000) / 10000000)
                            last_run_times.append(dt.isoformat())
                        except:
                            pass
            
            return {
                "filename": filename,
                "executable_name": executable_name,
                "run_count": run_count,
                "last_run_times": last_run_times,
                "last_run_time": last_run_times[0] if last_run_times else None,
                "version": "Vista/7",
                "prefetch_hash": filename.split('-')[-1].replace('.pf', '') if '-' in filename else ""
            }
            
        except Exception as e:
            print(f"Error parsing Vista/7 prefetch: {e}")
            return None

    def _parse_prefetch_v1E(self, pf_data, filename):
        """Parse Windows 8/8.1 prefetch format"""
        # Similar to Vista/7 but with slight differences
        return self._parse_prefetch_v1A(pf_data, filename)

    def _parse_prefetch_v1F(self, pf_data, filename):
        """Parse Windows 10 prefetch format"""
        # Similar to previous versions but may have additional fields
        return self._parse_prefetch_v1A(pf_data, filename)

    def parse_link_files(self, search_paths=None):
        """Parse Windows Link (.lnk) files"""
        if search_paths is None:
            search_paths = [
                "/Documents and Settings",
                "/Users"
            ]
        
        link_files = []
        
        for base_path in search_paths:
            # Recursively search for .lnk files
            link_files.extend(self._find_link_files_recursive(base_path))
        
        return link_files

    def _find_link_files_recursive(self, path, max_depth=5, current_depth=0):
        """Recursively find .lnk files"""
        if current_depth >= max_depth:
            return []
        
        link_files = []
        entries = self.list_directory_entries(path)
        
        for entry in entries:
            if entry["name"].lower().endswith(".lnk"):
                lnk_data = self.read_file_bytes(entry["path"])
                if lnk_data:
                    parsed_lnk = self._parse_link_file(lnk_data, entry["name"])
                    if parsed_lnk:
                        parsed_lnk["file_path"] = entry["path"]
                        parsed_lnk["file_size"] = entry["size"]
                        parsed_lnk["file_created"] = datetime.fromtimestamp(entry["created"]).isoformat() if entry["created"] else None
                        parsed_lnk["file_modified"] = datetime.fromtimestamp(entry["modified"]).isoformat() if entry["modified"] else None
                        link_files.append(parsed_lnk)
            
            # Recurse into subdirectories
            elif entry["name"] not in [".", ".."]:
                try:
                    subdir_links = self._find_link_files_recursive(entry["path"], max_depth, current_depth + 1)
                    link_files.extend(subdir_links)
                except:
                    continue
        
        return link_files

    def _parse_link_file(self, lnk_data, filename):
        """Parse Windows .lnk file"""
        try:
            if len(lnk_data) < 76:
                return None
            
            # Check for LNK signature
            signature = lnk_data[0:4]
            if signature != b'L\x00\x00\x00':
                return None
            
            # Parse shell link header
            link_clsid = lnk_data[4:20]
            link_flags = struct.unpack('<I', lnk_data[20:24])[0]
            file_attributes = struct.unpack('<I', lnk_data[24:28])[0]
            creation_time = struct.unpack('<Q', lnk_data[28:36])[0]
            access_time = struct.unpack('<Q', lnk_data[36:44])[0]
            write_time = struct.unpack('<Q', lnk_data[44:52])[0]
            file_size = struct.unpack('<I', lnk_data[52:56])[0]
            icon_index = struct.unpack('<I', lnk_data[56:60])[0]
            show_command = struct.unpack('<I', lnk_data[60:64])[0]
            
            # Convert FILETIME timestamps
            creation_dt = None
            access_dt = None
            write_dt = None
            
            if creation_time > 0:
                try:
                    creation_dt = datetime.fromtimestamp((creation_time - 116444736000000000) / 10000000)
                except:
                    pass
            
            if access_time > 0:
                try:
                    access_dt = datetime.fromtimestamp((access_time - 116444736000000000) / 10000000)
                except:
                    pass
            
            if write_time > 0:
                try:
                    write_dt = datetime.fromtimestamp((write_time - 116444736000000000) / 10000000)
                except:
                    pass
            
            # Parse optional structures
            offset = 76
            target_path = ""
            arguments = ""
            working_directory = ""
            icon_location = ""
            
            # LinkTarget IDList
            if link_flags & 0x01:  # HasLinkTargetIDList
                if offset + 2 <= len(lnk_data):
                    idlist_size = struct.unpack('<H', lnk_data[offset:offset+2])[0]
                    offset += 2 + idlist_size
            
            # LinkInfo structure
            if link_flags & 0x02:  # HasLinkInfo
                if offset + 4 <= len(lnk_data):
                    linkinfo_size = struct.unpack('<I', lnk_data[offset:offset+4])[0]
                    # Parse LinkInfo for target path
                    target_path = self._parse_linkinfo(lnk_data[offset:offset+linkinfo_size])
                    offset += linkinfo_size
            
            # String data
            if link_flags & 0x04:  # HasName
                name, offset = self._parse_string_data(lnk_data, offset)
            
            if link_flags & 0x08:  # HasRelativePath
                relative_path, offset = self._parse_string_data(lnk_data, offset)
            
            if link_flags & 0x10:  # HasWorkingDir
                working_directory, offset = self._parse_string_data(lnk_data, offset)
            
            if link_flags & 0x20:  # HasArguments
                arguments, offset = self._parse_string_data(lnk_data, offset)
            
            if link_flags & 0x40:  # HasIconLocation
                icon_location, offset = self._parse_string_data(lnk_data, offset)
            
            return {
                "filename": filename,
                "target_path": target_path,
                "arguments": arguments,
                "working_directory": working_directory,
                "icon_location": icon_location,
                "creation_time": creation_dt.isoformat() if creation_dt else None,
                "access_time": access_dt.isoformat() if access_dt else None,
                "write_time": write_dt.isoformat() if write_dt else None,
                "file_size": file_size,
                "file_attributes": file_attributes,
                "icon_index": icon_index,
                "show_command": show_command,
                "link_flags": link_flags
            }
            
        except Exception as e:
            print(f"Error parsing link file {filename}: {e}")
            return None

    def _parse_linkinfo(self, linkinfo_data):
        """Parse LinkInfo structure to extract target path"""
        try:
            if len(linkinfo_data) < 28:
                return ""
            
            linkinfo_flags = struct.unpack('<I', linkinfo_data[8:12])[0]
            
            # Check for local path
            if linkinfo_flags & 0x01:  # VolumeIDAndLocalBasePath
                local_base_path_offset = struct.unpack('<I', linkinfo_data[16:20])[0]
                if local_base_path_offset < len(linkinfo_data):
                    # Find null terminator
                    path_end = linkinfo_data.find(b'\x00', local_base_path_offset)
                    if path_end != -1:
                        return linkinfo_data[local_base_path_offset:path_end].decode('ascii', errors='ignore')
            
            # Check for network path
            if linkinfo_flags & 0x02:  # CommonNetworkRelativeLinkAndPathSuffix
                network_offset = struct.unpack('<I', linkinfo_data[20:24])[0]
                if network_offset < len(linkinfo_data):
                    path_end = linkinfo_data.find(b'\x00', network_offset)
                    if path_end != -1:
                        return linkinfo_data[network_offset:path_end].decode('ascii', errors='ignore')
            
        except Exception:
            pass
        
        return ""

    def _parse_string_data(self, lnk_data, offset):
        """Parse string data from link file"""
        try:
            if offset + 2 > len(lnk_data):
                return "", offset
            
            string_length = struct.unpack('<H', lnk_data[offset:offset+2])[0]
            offset += 2
            
            if offset + (string_length * 2) > len(lnk_data):
                return "", offset
            
            string_data = lnk_data[offset:offset+(string_length * 2)]
            string_value = string_data.decode('utf-16le', errors='ignore')
            offset += string_length * 2
            
            return string_value, offset
            
        except Exception:
            return "", offset

    def parse_jump_lists(self):
        """Parse Windows Jump Lists"""
        jump_lists = []
        
        # Jump list locations
        jump_list_paths = [
            "/Users/*/AppData/Roaming/Microsoft/Windows/Recent/AutomaticDestinations",
            "/Users/*/AppData/Roaming/Microsoft/Windows/Recent/CustomDestinations",
            "/Documents and Settings/*/Recent"
        ]
        
        for path_pattern in jump_list_paths:
            # This is a simplified approach - in practice, you'd need to expand wildcards
            base_path = path_pattern.replace("*", "").replace("/AutomaticDestinations", "").replace("/CustomDestinations", "")
            
            try:
                entries = self.list_directory_entries(base_path)
                for entry in entries:
                    if entry["name"].endswith(".automaticDestinations-ms") or entry["name"].endswith(".customDestinations-ms"):
                        # Jump list parsing would require OLE compound document parsing
                        # For now, we'll just record the existence and metadata
                        jump_lists.append({
                            "filename": entry["name"],
                            "path": entry["path"],
                            "size": entry["size"],
                            "created": datetime.fromtimestamp(entry["created"]).isoformat() if entry["created"] else None,
                            "modified": datetime.fromtimestamp(entry["modified"]).isoformat() if entry["modified"] else None,
                            "type": "automatic" if "automatic" in entry["name"].lower() else "custom"
                        })
            except:
                continue
        
        return jump_lists

    def parse_usn_journal(self):
        """Parse NTFS USN Journal"""
        # USN Journal is typically located at $Extend\$UsnJrnl:$J
        usn_path = "/$Extend/$UsnJrnl"
        
        try:
            # This is a complex structure that would require detailed NTFS knowledge
            # For now, we'll return a placeholder indicating the feature exists
            return {
                "status": "USN Journal parsing requires advanced NTFS structure analysis",
                "location": usn_path,
                "note": "This feature would parse file system change records"
            }
        except Exception as e:
            return {"error": f"USN Journal parsing error: {e}"}

    def extract_all_filesystem_artifacts(self):
        """Extract all file system artifacts"""
        artifacts = {
            "prefetch_files": [],
            "link_files": [],
            "jump_lists": [],
            "usn_journal": {},
            "summary": {
                "total_prefetch": 0,
                "total_links": 0,
                "total_jump_lists": 0
            }
        }
        
        try:
            # Parse prefetch files
            print("Parsing prefetch files...")
            artifacts["prefetch_files"] = self.parse_prefetch_files()
            artifacts["summary"]["total_prefetch"] = len(artifacts["prefetch_files"])
            
            # Parse link files
            print("Parsing link files...")
            artifacts["link_files"] = self.parse_link_files()
            artifacts["summary"]["total_links"] = len(artifacts["link_files"])
            
            # Parse jump lists
            print("Parsing jump lists...")
            artifacts["jump_lists"] = self.parse_jump_lists()
            artifacts["summary"]["total_jump_lists"] = len(artifacts["jump_lists"])
            
            # Parse USN Journal
            print("Analyzing USN Journal...")
            artifacts["usn_journal"] = self.parse_usn_journal()
            
        except Exception as e:
            print(f"Error extracting filesystem artifacts: {e}")
        
        return artifacts