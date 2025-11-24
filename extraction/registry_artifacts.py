#!/usr/bin/env python3
"""
registry_artifacts.py
Registry forensics module for USB history, UserAssist, installed programs, 
run keys, last logged-on user, timezone, and network info
"""

import os
import struct
import tempfile
from datetime import datetime, timedelta
from Registry import Registry
import codecs


class RegistryArtifacts:
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
    
    def write_temp(self, data, suffix=""):
        """Write bytes to temp file"""
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(data)
        tmp.close()
        return tmp.name
    
    def load_registry_hive(self, path):
        """Load registry hive from filesystem"""
        raw = self.read_file_bytes(path)
        if not raw:
            return None
            
        tmp = self.write_temp(raw, suffix=".reg")
        try:
            reg = Registry.Registry(tmp)
            os.remove(tmp)
            return reg
        except Exception as e:
            print(f"Failed to load registry hive {path}: {e}")
            try:
                os.remove(tmp)
            except:
                pass
            return None
    
    def _find_current_control_set(self, reg):
        """Find the current control set number"""
        try:
            # Get current control set from Select key
            select_key = reg.open("Select")
            current_value = select_key.value("Current")
            current_num = current_value.value()
            return f"ControlSet{current_num:03d}"
        except:
            # Fallback to ControlSet001 if Select key not found
            return "ControlSet001"

    def extract_usb_history(self, system_hive_path):
        """Extract USB device history from SYSTEM hive"""
        reg = self.load_registry_hive(system_hive_path)
        if not reg:
            return []
            
        usb_devices = []
        
        # Find the current control set
        current_control_set = self._find_current_control_set(reg)
        
        try:
            # USBSTOR entries
            usbstor_path = f"{current_control_set}\\Enum\\USBSTOR"
            usbstor_key = reg.open(usbstor_path)
            for device_key in usbstor_key.subkeys():
                device_name = device_key.name()
                
                for instance_key in device_key.subkeys():
                    instance_id = instance_key.name()
                    
                    device_info = {
                        "device_class": "USBSTOR",
                        "device_name": device_name,
                        "instance_id": instance_id,
                        "friendly_name": "",
                        "first_install": None,
                        "last_arrival": None,
                        "last_removal": None
                    }
                    
                    # Get friendly name
                    try:
                        friendly_name_val = instance_key.value("FriendlyName")
                        device_info["friendly_name"] = friendly_name_val.value()
                    except:
                        pass
                    
                    # Get timestamps
                    try:
                        device_info["first_install"] = instance_key.timestamp().isoformat()
                    except:
                        pass
                    
                    usb_devices.append(device_info)
                    
        except Exception as e:
            print(f"Error extracting USBSTOR: {e}")
        
        try:
            # USB entries for additional info
            usb_path = f"{current_control_set}\\Enum\\USB"
            usb_key = reg.open(usb_path)
            for device_key in usb_key.subkeys():
                device_name = device_key.name()
                
                for instance_key in device_key.subkeys():
                    instance_id = instance_key.name()
                    
                    device_info = {
                        "device_class": "USB",
                        "device_name": device_name,
                        "instance_id": instance_id,
                        "friendly_name": "",
                        "first_install": None
                    }
                    
                    try:
                        friendly_name_val = instance_key.value("FriendlyName")
                        device_info["friendly_name"] = friendly_name_val.value()
                    except:
                        pass
                    
                    try:
                        device_info["first_install"] = instance_key.timestamp().isoformat()
                    except:
                        pass
                    
                    usb_devices.append(device_info)
                    
        except Exception as e:
            print(f"Error extracting USB: {e}")
            
        return usb_devices

    def extract_userassist(self, ntuser_path):
        """Extract UserAssist entries (GUI programs run by user)"""
        reg = self.load_registry_hive(ntuser_path)
        if not reg:
            return []
            
        userassist_entries = []
        
        try:
            # UserAssist is stored under Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist
            # Try different possible paths
            userassist_paths = [
                "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist",
                "Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist"
            ]
            
            userassist_key = None
            for path in userassist_paths:
                try:
                    userassist_key = reg.open(path)
                    break
                except:
                    continue
            
            if not userassist_key:
                return []
            
            for guid_key in userassist_key.subkeys():
                guid = guid_key.name()
                
                try:
                    count_key = guid_key.subkey("Count")
                    
                    for value in count_key.values():
                        value_name = value.name()
                        value_data = value.value()
                        
                        # Decode ROT13 encoded program name
                        try:
                            decoded_name = codecs.decode(value_name, 'rot13')
                        except:
                            decoded_name = value_name
                        
                        # Parse UserAssist data structure
                        if len(value_data) >= 16:
                            try:
                                # Windows 7+ format
                                if len(value_data) >= 72:
                                    run_count = struct.unpack('<I', value_data[4:8])[0]
                                    last_run_time = struct.unpack('<Q', value_data[60:68])[0]
                                    
                                    # Convert Windows FILETIME to datetime
                                    if last_run_time > 0:
                                        last_run_dt = datetime.fromtimestamp((last_run_time - 116444736000000000) / 10000000)
                                    else:
                                        last_run_dt = None
                                        
                                # Windows XP format
                                else:
                                    run_count = struct.unpack('<I', value_data[4:8])[0]
                                    last_run_time = struct.unpack('<Q', value_data[8:16])[0]
                                    
                                    if last_run_time > 0:
                                        last_run_dt = datetime.fromtimestamp((last_run_time - 116444736000000000) / 10000000)
                                    else:
                                        last_run_dt = None
                                
                                userassist_entries.append({
                                    "guid": guid,
                                    "program": decoded_name,
                                    "run_count": run_count,
                                    "last_run": last_run_dt.isoformat() if last_run_dt else None
                                })
                                
                            except Exception as e:
                                print(f"Error parsing UserAssist data for {decoded_name}: {e}")
                                
                except Exception as e:
                    print(f"Error processing UserAssist GUID {guid}: {e}")
                    
        except Exception as e:
            print(f"Error extracting UserAssist: {e}")
            
        return userassist_entries

    def extract_installed_programs(self, software_hive_path):
        """Extract installed programs from SOFTWARE hive"""
        reg = self.load_registry_hive(software_hive_path)
        if not reg:
            return []
            
        programs = []
        
        # Check multiple locations for installed programs
        uninstall_paths = [
            "Microsoft\\Windows\\CurrentVersion\\Uninstall",
            "Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
        ]
        
        for uninstall_path in uninstall_paths:
            try:
                uninstall_key = reg.open(uninstall_path)
                
                for program_key in uninstall_key.subkeys():
                    program_info = {
                        "registry_key": program_key.name(),
                        "display_name": "",
                        "display_version": "",
                        "publisher": "",
                        "install_date": "",
                        "install_location": "",
                        "uninstall_string": "",
                        "estimated_size": 0
                    }
                    
                    # Extract program information
                    for value_name in ["DisplayName", "DisplayVersion", "Publisher", 
                                     "InstallDate", "InstallLocation", "UninstallString", "EstimatedSize"]:
                        try:
                            value = program_key.value(value_name)
                            program_info[value_name.lower().replace("display", "display_")] = value.value()
                        except:
                            pass
                    
                    # Only add if we have a display name
                    if program_info["display_name"]:
                        programs.append(program_info)
                        
            except Exception as e:
                print(f"Error extracting from {uninstall_path}: {e}")
                
        return programs

    def extract_run_keys(self, software_hive_path, ntuser_paths):
        """Extract Run keys (persistence mechanisms)"""
        run_entries = []
        
        # System-wide run keys from SOFTWARE hive
        software_reg = self.load_registry_hive(software_hive_path)
        if software_reg:
            system_run_paths = [
                "Microsoft\\Windows\\CurrentVersion\\Run",
                "Microsoft\\Windows\\CurrentVersion\\RunOnce",
                "Microsoft\\Windows\\CurrentVersion\\RunServices",
                "Microsoft\\Windows\\CurrentVersion\\RunServicesOnce",
                "Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Run",
                "Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\RunOnce"
            ]
            
            for run_path in system_run_paths:
                try:
                    run_key = software_reg.open(run_path)
                    
                    for value in run_key.values():
                        run_entries.append({
                            "hive": "SOFTWARE",
                            "key_path": run_path,
                            "name": value.name(),
                            "value": value.value(),
                            "type": "system"
                        })
                        
                except Exception:
                    continue
        
        # User-specific run keys from NTUSER.DAT files
        for ntuser_path in ntuser_paths:
            ntuser_reg = self.load_registry_hive(ntuser_path)
            if not ntuser_reg:
                continue
                
            user_run_paths = [
                "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                "Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce"
            ]
            
            for run_path in user_run_paths:
                try:
                    run_key = ntuser_reg.open(run_path)
                    
                    for value in run_key.values():
                        run_entries.append({
                            "hive": ntuser_path,
                            "key_path": run_path,
                            "name": value.name(),
                            "value": value.value(),
                            "type": "user"
                        })
                        
                except Exception:
                    continue
                    
        return run_entries

    def extract_last_logged_user(self, software_hive_path):
        """Extract last logged-on user information"""
        reg = self.load_registry_hive(software_hive_path)
        if not reg:
            return {}
            
        user_info = {}
        
        try:
            # Windows Logon key
            logon_key = reg.open("Microsoft\\Windows NT\\CurrentVersion\\Winlogon")
            
            for value_name in ["DefaultUserName", "DefaultDomainName", "LastUsedUsername"]:
                try:
                    value = logon_key.value(value_name)
                    user_info[value_name.lower()] = value.value()
                except:
                    pass
                    
        except Exception as e:
            print(f"Error extracting last logged user: {e}")
            
        return user_info

    def extract_timezone_info(self, system_hive_path):
        """Extract timezone information"""
        reg = self.load_registry_hive(system_hive_path)
        if not reg:
            return {}
            
        timezone_info = {}
        
        # Find the current control set
        current_control_set = self._find_current_control_set(reg)
        
        try:
            # Current timezone
            timezone_path = f"{current_control_set}\\Control\\TimeZoneInformation"
            timezone_key = reg.open(timezone_path)
            
            for value in timezone_key.values():
                value_name = value.name()
                value_data = value.value()
                
                if value_name in ["TimeZoneKeyName", "StandardName", "DaylightName"]:
                    timezone_info[value_name.lower()] = value_data
                elif value_name in ["Bias", "StandardBias", "DaylightBias"]:
                    timezone_info[value_name.lower()] = value_data
                    
        except Exception as e:
            print(f"Error extracting timezone info: {e}")
            
        return timezone_info

    def extract_network_info(self, system_hive_path):
        """Extract network configuration information"""
        reg = self.load_registry_hive(system_hive_path)
        if not reg:
            return {}
            
        network_info = {
            "network_adapters": [],
            "tcp_parameters": {},
            "wireless_networks": []
        }
        
        # Find the current control set
        current_control_set = self._find_current_control_set(reg)
        
        try:
            # Network adapters
            adapters_path = f"{current_control_set}\\Control\\Class\\{{4D36E972-E325-11CE-BFC1-08002BE10318}}"
            adapters_key = reg.open(adapters_path)
            
            for adapter_key in adapters_key.subkeys():
                if adapter_key.name().isdigit():
                    adapter_info = {}
                    
                    for value_name in ["DriverDesc", "DriverVersion", "DriverDate", "NetCfgInstanceId"]:
                        try:
                            value = adapter_key.value(value_name)
                            adapter_info[value_name.lower()] = value.value()
                        except:
                            pass
                    
                    if adapter_info:
                        network_info["network_adapters"].append(adapter_info)
                        
        except Exception as e:
            print(f"Error extracting network adapters: {e}")
        
        try:
            # TCP/IP parameters
            tcpip_path = f"{current_control_set}\\Services\\Tcpip\\Parameters"
            tcpip_key = reg.open(tcpip_path)
            
            for value in tcpip_key.values():
                value_name = value.name()
                if value_name in ["Hostname", "Domain", "DhcpDomain", "SearchList"]:
                    network_info["tcp_parameters"][value_name.lower()] = value.value()
                    
        except Exception as e:
            print(f"Error extracting TCP/IP parameters: {e}")
            
        return network_info

    def extract_all_registry_artifacts(self, system_hive_path, software_hive_path, ntuser_paths):
        """Extract all registry artifacts"""
        artifacts = {
            "usb_history": [],
            "userassist": [],
            "installed_programs": [],
            "run_keys": [],
            "last_logged_user": {},
            "timezone_info": {},
            "network_info": {}
        }
        
        try:
            # USB history from SYSTEM hive
            artifacts["usb_history"] = self.extract_usb_history(system_hive_path)
            
            # UserAssist from NTUSER.DAT files
            for ntuser_path in ntuser_paths:
                userassist = self.extract_userassist(ntuser_path)
                artifacts["userassist"].extend(userassist)
            
            # Installed programs from SOFTWARE hive
            artifacts["installed_programs"] = self.extract_installed_programs(software_hive_path)
            
            # Run keys from SOFTWARE and NTUSER hives
            artifacts["run_keys"] = self.extract_run_keys(software_hive_path, ntuser_paths)
            
            # Last logged user from SOFTWARE hive
            artifacts["last_logged_user"] = self.extract_last_logged_user(software_hive_path)
            
            # Timezone info from SYSTEM hive
            artifacts["timezone_info"] = self.extract_timezone_info(system_hive_path)
            
            # Network info from SYSTEM hive
            artifacts["network_info"] = self.extract_network_info(system_hive_path)
            
        except Exception as e:
            print(f"Error extracting registry artifacts: {e}")
            
        return artifacts