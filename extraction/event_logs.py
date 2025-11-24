#!/usr/bin/env python3
"""
event_logs.py
Windows Event Log forensics module for parsing .evt (XP format) and .evtx files,
extracting logon events, system startup, and service failures
"""

import os
import struct
from datetime import datetime
import tempfile


class EventLogArtifacts:
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
    
    def list_event_log_files(self):
        """List all event log files in the system"""
        log_files = []
        
        # Common event log locations
        log_paths = [
            "/Windows/System32/winevt/Logs",  # Vista+ .evtx files
            "/Windows/System32/config",       # XP .evt files
            "/WINNT/System32/config"          # Windows 2000 .evt files
        ]
        
        for log_path in log_paths:
            try:
                directory = self.fs.open_dir(log_path)
                for entry in directory:
                    try:
                        name = entry.info.name.name.decode(errors="ignore")
                        if name.lower().endswith(('.evt', '.evtx')):
                            log_files.append({
                                "name": name,
                                "path": os.path.join(log_path, name),
                                "size": entry.info.meta.size if entry.info.meta else 0,
                                "type": "evtx" if name.lower().endswith('.evtx') else "evt"
                            })
                    except Exception:
                        continue
            except Exception:
                continue
                
        return log_files

    def parse_evt_file(self, evt_path):
        """Parse Windows XP/2000 .evt file format"""
        raw_data = self.read_file_bytes(evt_path)
        if not raw_data:
            return []
            
        events = []
        
        try:
            # EVT file header
            if len(raw_data) < 48:
                return []
            
            # Check for EVT signature - try multiple possible signatures
            signature = raw_data[0:4]
            if signature not in [b'LfLe', b'ElfF']:
                # Try to find signature elsewhere in the file
                found_signature = False
                for i in range(0, min(512, len(raw_data) - 4), 4):
                    if raw_data[i:i+4] in [b'LfLe', b'ElfF']:
                        print(f"Found EVT signature at offset {i} in {evt_path}")
                        raw_data = raw_data[i:]  # Adjust data to start from signature
                        found_signature = True
                        break
                
                if not found_signature:
                    print(f"No valid EVT signature found in {evt_path}")
                    return []
            
            # Parse header
            header_size = struct.unpack('<I', raw_data[4:8])[0]
            oldest_record = struct.unpack('<I', raw_data[16:20])[0]
            next_record = struct.unpack('<I', raw_data[20:24])[0]
            
            # Start parsing records after header
            offset = header_size
            
            while offset < len(raw_data) - 8:
                try:
                    # Check for record signature
                    if raw_data[offset:offset+4] != b'LfLe':
                        offset += 1
                        continue
                    
                    # Parse record header
                    record_length = struct.unpack('<I', raw_data[offset+4:offset+8])[0]
                    
                    if record_length < 56 or offset + record_length > len(raw_data):
                        offset += 8
                        continue
                    
                    record_data = raw_data[offset:offset+record_length]
                    event = self._parse_evt_record(record_data)
                    
                    if event:
                        events.append(event)
                    
                    offset += record_length
                    
                except Exception as e:
                    print(f"Error parsing EVT record at offset {offset}: {e}")
                    offset += 1
                    
        except Exception as e:
            print(f"Error parsing EVT file {evt_path}: {e}")
            
        return events

    def _parse_evt_record(self, record_data):
        """Parse individual EVT record"""
        try:
            if len(record_data) < 56:
                return None
            
            # Parse fixed portion of record
            record_length = struct.unpack('<I', record_data[4:8])[0]
            record_number = struct.unpack('<I', record_data[8:12])[0]
            time_generated = struct.unpack('<I', record_data[12:16])[0]
            time_written = struct.unpack('<I', record_data[16:20])[0]
            event_id = struct.unpack('<I', record_data[20:24])[0]
            event_type = struct.unpack('<H', record_data[24:26])[0]
            num_strings = struct.unpack('<H', record_data[26:28])[0]
            event_category = struct.unpack('<H', record_data[28:30])[0]
            
            # Skip reserved fields and get string offset
            string_offset = struct.unpack('<I', record_data[36:40])[0]
            user_sid_length = struct.unpack('<I', record_data[40:44])[0]
            user_sid_offset = struct.unpack('<I', record_data[44:48])[0]
            data_length = struct.unpack('<I', record_data[48:52])[0]
            data_offset = struct.unpack('<I', record_data[52:56])[0]
            
            # Extract source name (null-terminated string after fixed header)
            source_start = 56
            source_end = record_data.find(b'\x00\x00', source_start)
            if source_end == -1:
                source_name = ""
            else:
                try:
                    source_name = record_data[source_start:source_end].decode('utf-16le', errors='ignore')
                except:
                    source_name = record_data[source_start:source_end].decode('ascii', errors='ignore')
            
            # Extract computer name
            computer_start = source_end + 2 if source_end != -1 else source_start
            computer_end = record_data.find(b'\x00\x00', computer_start)
            if computer_end == -1:
                computer_name = ""
            else:
                try:
                    computer_name = record_data[computer_start:computer_end].decode('utf-16le', errors='ignore')
                except:
                    computer_name = record_data[computer_start:computer_end].decode('ascii', errors='ignore')
            
            # Extract strings
            strings = []
            if string_offset < len(record_data) and num_strings > 0:
                string_data = record_data[string_offset:]
                current_pos = 0
                
                for i in range(num_strings):
                    if current_pos >= len(string_data):
                        break
                    
                    # Find null terminator
                    null_pos = string_data.find(b'\x00\x00', current_pos)
                    if null_pos == -1:
                        break
                    
                    try:
                        string_val = string_data[current_pos:null_pos].decode('utf-16le', errors='ignore')
                    except:
                        string_val = string_data[current_pos:null_pos].decode('ascii', errors='ignore')
                    
                    strings.append(string_val)
                    current_pos = null_pos + 2
            
            # Convert timestamps
            time_generated_dt = datetime.fromtimestamp(time_generated) if time_generated else None
            time_written_dt = datetime.fromtimestamp(time_written) if time_written else None
            
            # Map event types
            event_type_map = {
                1: "Error",
                2: "Warning", 
                4: "Information",
                8: "Success Audit",
                16: "Failure Audit"
            }
            
            return {
                "record_number": record_number,
                "event_id": event_id,
                "event_type": event_type_map.get(event_type, f"Unknown({event_type})"),
                "event_category": event_category,
                "time_generated": time_generated_dt.isoformat() if time_generated_dt else None,
                "time_written": time_written_dt.isoformat() if time_written_dt else None,
                "source_name": source_name,
                "computer_name": computer_name,
                "strings": strings,
                "user_sid_length": user_sid_length,
                "data_length": data_length
            }
            
        except Exception as e:
            print(f"Error parsing EVT record: {e}")
            return None

    def extract_logon_events(self, events):
        """Extract logon-related events"""
        logon_events = []
        
        # Common logon event IDs
        logon_event_ids = {
            528: "Successful Logon",
            529: "Logon Failure - Unknown user name or bad password",
            530: "Logon Failure - Account logon time restriction violation",
            531: "Logon Failure - Account currently disabled",
            532: "Logon Failure - The specified user account has expired",
            533: "Logon Failure - User not allowed to logon at this computer",
            534: "Logon Failure - The user has not been granted the requested logon type",
            535: "Logon Failure - The specified account's password has expired",
            536: "Logon Failure - The NetLogon service is not active",
            537: "Logon Failure - Unknown reason",
            538: "User Logoff",
            539: "Logon Failure - Account locked out",
            540: "Successful Network Logon",
            4624: "An account was successfully logged on",  # Vista+
            4625: "An account failed to log on",            # Vista+
            4634: "An account was logged off",              # Vista+
            4647: "User initiated logoff",                  # Vista+
            4648: "A logon was attempted using explicit credentials"  # Vista+
        }
        
        for event in events:
            if event["event_id"] in logon_event_ids:
                logon_event = event.copy()
                logon_event["event_description"] = logon_event_ids[event["event_id"]]
                
                # Extract additional logon information from strings
                if event["strings"]:
                    logon_event["logon_details"] = self._parse_logon_strings(event["event_id"], event["strings"])
                
                logon_events.append(logon_event)
        
        return logon_events

    def _parse_logon_strings(self, event_id, strings):
        """Parse logon event strings for additional details"""
        details = {}
        
        try:
            if event_id in [528, 540, 4624]:  # Successful logon
                if len(strings) >= 8:
                    details["user_name"] = strings[0] if len(strings) > 0 else ""
                    details["domain"] = strings[1] if len(strings) > 1 else ""
                    details["logon_id"] = strings[2] if len(strings) > 2 else ""
                    details["logon_type"] = strings[3] if len(strings) > 3 else ""
                    details["logon_process"] = strings[4] if len(strings) > 4 else ""
                    details["authentication_package"] = strings[5] if len(strings) > 5 else ""
                    details["workstation_name"] = strings[6] if len(strings) > 6 else ""
                    details["source_network_address"] = strings[7] if len(strings) > 7 else ""
                    
            elif event_id in [529, 530, 531, 532, 533, 534, 535, 536, 537, 539, 4625]:  # Failed logon
                if len(strings) >= 6:
                    details["user_name"] = strings[0] if len(strings) > 0 else ""
                    details["domain"] = strings[1] if len(strings) > 1 else ""
                    details["failure_reason"] = strings[2] if len(strings) > 2 else ""
                    details["status"] = strings[3] if len(strings) > 3 else ""
                    details["sub_status"] = strings[4] if len(strings) > 4 else ""
                    details["workstation_name"] = strings[5] if len(strings) > 5 else ""
                    
            elif event_id in [538, 4634, 4647]:  # Logoff
                if len(strings) >= 3:
                    details["user_name"] = strings[0] if len(strings) > 0 else ""
                    details["domain"] = strings[1] if len(strings) > 1 else ""
                    details["logon_id"] = strings[2] if len(strings) > 2 else ""
                    
        except Exception as e:
            print(f"Error parsing logon strings: {e}")
            
        return details

    def extract_system_events(self, events):
        """Extract system startup, shutdown, and service events"""
        system_events = []
        
        # System event IDs
        system_event_ids = {
            6005: "The Event log service was started",
            6006: "The Event log service was stopped", 
            6009: "System startup",
            6013: "System uptime",
            1074: "System shutdown initiated by user",
            1076: "System shutdown reason",
            6008: "Unexpected system shutdown",
            7034: "Service crashed unexpectedly",
            7035: "Service sent a control",
            7036: "Service started or stopped",
            7040: "Service start type changed"
        }
        
        for event in events:
            if event["event_id"] in system_event_ids:
                system_event = event.copy()
                system_event["event_description"] = system_event_ids[event["event_id"]]
                
                # Parse service-specific information
                if event["event_id"] in [7034, 7035, 7036, 7040] and event["strings"]:
                    system_event["service_name"] = event["strings"][0] if len(event["strings"]) > 0 else ""
                    if event["event_id"] == 7036 and len(event["strings"]) > 1:
                        system_event["service_state"] = event["strings"][1]
                
                system_events.append(system_event)
        
        return system_events

    def extract_all_event_log_artifacts(self):
        """Extract all event log artifacts"""
        artifacts = {
            "log_files": [],
            "all_events": [],
            "logon_events": [],
            "system_events": [],
            "summary": {
                "total_events": 0,
                "total_logon_events": 0,
                "total_system_events": 0,
                "date_range": {"earliest": None, "latest": None}
            }
        }
        
        # Find all event log files
        log_files = self.list_event_log_files()
        artifacts["log_files"] = log_files
        
        all_events = []
        event_times = []
        
        # Parse each log file
        for log_file in log_files:
            print(f"Parsing event log: {log_file['name']}")
            
            if log_file["type"] == "evt":
                events = self.parse_evt_file(log_file["path"])
                all_events.extend(events)
                
                # Collect timestamps
                for event in events:
                    if event.get("time_generated"):
                        event_times.append(event["time_generated"])
            
            # Note: .evtx parsing would require additional libraries like python-evtx
            # For now, we focus on .evt files which are more common in older systems
        
        artifacts["all_events"] = all_events
        
        # Extract specific event types
        artifacts["logon_events"] = self.extract_logon_events(all_events)
        artifacts["system_events"] = self.extract_system_events(all_events)
        
        # Update summary
        artifacts["summary"]["total_events"] = len(all_events)
        artifacts["summary"]["total_logon_events"] = len(artifacts["logon_events"])
        artifacts["summary"]["total_system_events"] = len(artifacts["system_events"])
        
        if event_times:
            event_times.sort()
            artifacts["summary"]["date_range"]["earliest"] = event_times[0]
            artifacts["summary"]["date_range"]["latest"] = event_times[-1]
        
        return artifacts

    def search_events_by_user(self, username):
        """Search for events related to specific user"""
        all_artifacts = self.extract_all_event_log_artifacts()
        user_events = []
        
        for event in all_artifacts["all_events"]:
            # Check in strings for username
            if event.get("strings"):
                for string in event["strings"]:
                    if username.lower() in string.lower():
                        user_events.append(event)
                        break
        
        return user_events

    def search_events_by_date_range(self, start_date, end_date):
        """Search for events within date range"""
        all_artifacts = self.extract_all_event_log_artifacts()
        matching_events = []
        
        for event in all_artifacts["all_events"]:
            event_time = event.get("time_generated")
            if event_time and start_date <= event_time <= end_date:
                matching_events.append(event)
        
        return matching_events