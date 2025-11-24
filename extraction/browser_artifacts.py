#!/usr/bin/env python3
"""
browser_artifacts.py
Enhanced browser forensics module for Firefox, Chrome, Edge, and Internet Explorer
"""

import os
import json
import sqlite3
import tempfile
import struct
from datetime import datetime, timedelta
import urllib.parse


class BrowserArtifacts:
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

    def extract_firefox_artifacts(self, user_profile_path):
        """Extract Firefox history, cookies, and downloads"""
        base = os.path.join(user_profile_path, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
        results = {"history": [], "cookies": [], "downloads": []}
        
        try:
            d = self.fs.open_dir(base)
        except Exception:
            return results
            
        for entry in d:
            try:
                name = entry.info.name.name.decode(errors="ignore")
                if name in [".", ".."]:
                    continue
                    
                profile_path = os.path.join(base, name)
                
                # History from places.sqlite
                places_path = os.path.join(profile_path, "places.sqlite")
                history = self._extract_firefox_history(places_path)
                results["history"].extend(history)
                
                # Cookies from cookies.sqlite
                cookies_path = os.path.join(profile_path, "cookies.sqlite")
                cookies = self._extract_firefox_cookies(cookies_path)
                results["cookies"].extend(cookies)
                
                # Downloads from places.sqlite
                downloads = self._extract_firefox_downloads(places_path)
                results["downloads"].extend(downloads)
                
            except Exception:
                continue
                
        return results
    
    def _extract_firefox_history(self, places_path):
        """Extract Firefox browsing history"""
        raw = self.read_file_bytes(places_path)
        if not raw:
            return []
            
        tmp = self.write_temp(raw, suffix=".sqlite")
        history = []
        
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            
            query = """
            SELECT url, title, visit_count, last_visit_date, 
                   typed, hidden, frecency
            FROM moz_places 
            WHERE last_visit_date IS NOT NULL 
            ORDER BY last_visit_date DESC 
            LIMIT 1000
            """
            
            cur.execute(query)
            for row in cur.fetchall():
                url, title, visit_count, last_visit, typed, hidden, frecency = row
                
                # Convert Firefox timestamp (microseconds since 1970)
                if last_visit:
                    timestamp = datetime.fromtimestamp(last_visit / 1000000)
                else:
                    timestamp = None
                    
                history.append({
                    "source": "firefox",
                    "url": url,
                    "title": title,
                    "visit_count": visit_count,
                    "last_visit": timestamp.isoformat() if timestamp else None,
                    "typed": bool(typed),
                    "hidden": bool(hidden),
                    "frecency": frecency
                })
                
        except Exception as e:
            print(f"Firefox history extraction error: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            os.remove(tmp)
            
        return history
    
    def _extract_firefox_cookies(self, cookies_path):
        """Extract Firefox cookies"""
        raw = self.read_file_bytes(cookies_path)
        if not raw:
            return []
            
        tmp = self.write_temp(raw, suffix=".sqlite")
        cookies = []
        
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            
            query = """
            SELECT name, value, host, path, expiry, 
                   lastAccessed, creationTime, isSecure, isHttpOnly
            FROM moz_cookies
            ORDER BY lastAccessed DESC
            """
            
            cur.execute(query)
            for row in cur.fetchall():
                name, value, host, path, expiry, last_accessed, creation_time, is_secure, is_http_only = row
                
                cookies.append({
                    "source": "firefox",
                    "name": name,
                    "value": value,
                    "host": host,
                    "path": path,
                    "expiry": datetime.fromtimestamp(expiry).isoformat() if expiry else None,
                    "last_accessed": datetime.fromtimestamp(last_accessed / 1000000).isoformat() if last_accessed else None,
                    "creation_time": datetime.fromtimestamp(creation_time / 1000000).isoformat() if creation_time else None,
                    "is_secure": bool(is_secure),
                    "is_http_only": bool(is_http_only)
                })
                
        except Exception as e:
            print(f"Firefox cookies extraction error: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            os.remove(tmp)
            
        return cookies
    
    def _extract_firefox_downloads(self, places_path):
        """Extract Firefox downloads from places.sqlite"""
        raw = self.read_file_bytes(places_path)
        if not raw:
            return []
            
        tmp = self.write_temp(raw, suffix=".sqlite")
        downloads = []
        
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            
            # Downloads are stored in moz_annos table with specific annotations
            query = """
            SELECT p.url, p.title, a.content, p.last_visit_date
            FROM moz_places p
            JOIN moz_annos a ON p.id = a.place_id
            JOIN moz_anno_attributes aa ON a.anno_attribute_id = aa.id
            WHERE aa.name = 'downloads/destinationFileURI'
            ORDER BY p.last_visit_date DESC
            """
            
            cur.execute(query)
            for row in cur.fetchall():
                url, title, destination, last_visit = row
                
                downloads.append({
                    "source": "firefox",
                    "url": url,
                    "title": title,
                    "destination": destination,
                    "download_time": datetime.fromtimestamp(last_visit / 1000000).isoformat() if last_visit else None
                })
                
        except Exception as e:
            print(f"Firefox downloads extraction error: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            os.remove(tmp)
            
        return downloads

    def extract_chrome_edge_artifacts(self, user_profile_path):
        """Extract Chrome/Edge history, cookies, and downloads"""
        browsers = {
            "chrome": os.path.join(user_profile_path, "AppData", "Local", "Google", "Chrome", "User Data", "Default"),
            "edge": os.path.join(user_profile_path, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default")
        }
        
        results = {"history": [], "cookies": [], "downloads": []}
        
        for browser_name, profile_path in browsers.items():
            # History
            history_path = os.path.join(profile_path, "History")
            history = self._extract_chromium_history(history_path, browser_name)
            results["history"].extend(history)
            
            # Cookies
            cookies_path = os.path.join(profile_path, "Cookies")
            cookies = self._extract_chromium_cookies(cookies_path, browser_name)
            results["cookies"].extend(cookies)
            
            # Downloads are in History database
            downloads = self._extract_chromium_downloads(history_path, browser_name)
            results["downloads"].extend(downloads)
            
        return results
    
    def _extract_chromium_history(self, history_path, browser_name):
        """Extract Chromium-based browser history"""
        raw = self.read_file_bytes(history_path)
        if not raw:
            return []
            
        tmp = self.write_temp(raw, suffix=".sqlite")
        history = []
        
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            
            query = """
            SELECT url, title, visit_count, last_visit_time, typed_count
            FROM urls 
            ORDER BY last_visit_time DESC 
            LIMIT 1000
            """
            
            cur.execute(query)
            for row in cur.fetchall():
                url, title, visit_count, last_visit_time, typed_count = row
                
                # Convert Chrome timestamp (microseconds since 1601-01-01)
                if last_visit_time:
                    # Chrome epoch starts at 1601-01-01
                    chrome_epoch = datetime(1601, 1, 1)
                    timestamp = chrome_epoch + timedelta(microseconds=last_visit_time)
                else:
                    timestamp = None
                    
                history.append({
                    "source": browser_name,
                    "url": url,
                    "title": title,
                    "visit_count": visit_count,
                    "last_visit": timestamp.isoformat() if timestamp else None,
                    "typed_count": typed_count
                })
                
        except Exception as e:
            print(f"{browser_name} history extraction error: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            os.remove(tmp)
            
        return history
    
    def _extract_chromium_cookies(self, cookies_path, browser_name):
        """Extract Chromium-based browser cookies"""
        raw = self.read_file_bytes(cookies_path)
        if not raw:
            return []
            
        tmp = self.write_temp(raw, suffix=".sqlite")
        cookies = []
        
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            
            query = """
            SELECT name, value, host_key, path, expires_utc, 
                   last_access_utc, creation_utc, is_secure, is_httponly
            FROM cookies
            ORDER BY last_access_utc DESC
            """
            
            cur.execute(query)
            for row in cur.fetchall():
                name, value, host_key, path, expires_utc, last_access_utc, creation_utc, is_secure, is_httponly = row
                
                # Convert Chrome timestamps
                chrome_epoch = datetime(1601, 1, 1)
                
                cookies.append({
                    "source": browser_name,
                    "name": name,
                    "value": value,
                    "host": host_key,
                    "path": path,
                    "expires": (chrome_epoch + timedelta(microseconds=expires_utc)).isoformat() if expires_utc else None,
                    "last_access": (chrome_epoch + timedelta(microseconds=last_access_utc)).isoformat() if last_access_utc else None,
                    "creation": (chrome_epoch + timedelta(microseconds=creation_utc)).isoformat() if creation_utc else None,
                    "is_secure": bool(is_secure),
                    "is_httponly": bool(is_httponly)
                })
                
        except Exception as e:
            print(f"{browser_name} cookies extraction error: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            os.remove(tmp)
            
        return cookies
    
    def _extract_chromium_downloads(self, history_path, browser_name):
        """Extract Chromium-based browser downloads"""
        raw = self.read_file_bytes(history_path)
        if not raw:
            return []
            
        tmp = self.write_temp(raw, suffix=".sqlite")
        downloads = []
        
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            
            query = """
            SELECT current_path, target_path, start_time, end_time, 
                   received_bytes, total_bytes, state, danger_type, url
            FROM downloads
            ORDER BY start_time DESC
            """
            
            cur.execute(query)
            for row in cur.fetchall():
                current_path, target_path, start_time, end_time, received_bytes, total_bytes, state, danger_type, url = row
                
                chrome_epoch = datetime(1601, 1, 1)
                
                downloads.append({
                    "source": browser_name,
                    "url": url,
                    "current_path": current_path,
                    "target_path": target_path,
                    "start_time": (chrome_epoch + timedelta(microseconds=start_time)).isoformat() if start_time else None,
                    "end_time": (chrome_epoch + timedelta(microseconds=end_time)).isoformat() if end_time else None,
                    "received_bytes": received_bytes,
                    "total_bytes": total_bytes,
                    "state": state,
                    "danger_type": danger_type
                })
                
        except Exception as e:
            print(f"{browser_name} downloads extraction error: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
            os.remove(tmp)
            
        return downloads

    def extract_ie_artifacts(self, user_profile_path):
        """Extract Internet Explorer artifacts from index.dat files"""
        results = {"history": [], "cookies": []}
        
        # Common IE cache locations - try multiple variations
        ie_paths = [
            # Windows XP/2000 locations
            os.path.join(user_profile_path, "Local Settings", "History", "History.IE5", "index.dat"),
            os.path.join(user_profile_path, "Local Settings", "Temporary Internet Files", "Content.IE5", "index.dat"),
            os.path.join(user_profile_path, "Cookies", "index.dat"),
            # Alternative locations
            os.path.join(user_profile_path, "Local Settings", "History", "index.dat"),
            os.path.join(user_profile_path, "Local Settings", "Temporary Internet Files", "index.dat"),
            # Check for subdirectories in History.IE5
            os.path.join(user_profile_path, "Local Settings", "History", "History.IE5"),
            os.path.join(user_profile_path, "Local Settings", "Temporary Internet Files", "Content.IE5")
        ]
        
        for path in ie_paths:
            # If it's a directory, look for index.dat files inside
            if path.endswith(("History.IE5", "Content.IE5")):
                try:
                    entries = self.list_directory_entries(path)
                    for entry in entries:
                        if entry["name"].lower() == "index.dat":
                            raw = self.read_file_bytes(entry["path"])
                            if raw:
                                parsed = self._parse_index_dat(raw)
                                if "History.IE5" in path:
                                    results["history"].extend(parsed)
                                elif "Content.IE5" in path:
                                    results["cookies"].extend(parsed)
                except:
                    continue
            else:
                # Direct file path
                raw = self.read_file_bytes(path)
                if raw:
                    parsed = self._parse_index_dat(raw)
                    if "History" in path:
                        results["history"].extend(parsed)
                    elif "Cookies" in path:
                        results["cookies"].extend(parsed)
                    elif "Content" in path:
                        results["cookies"].extend(parsed)
                    
        return results
    
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
                            "size": entry.info.meta.size if entry.info.meta else 0
                        })
                except Exception:
                    continue
            return entries
        except Exception:
            return []
    
    def _parse_index_dat(self, data):
        """Parse IE index.dat file format"""
        entries = []
        
        try:
            # Basic index.dat parsing - improved version
            offset = 0
            while offset < len(data) - 64:
                # Look for URL record signature
                if data[offset:offset+4] == b'URL ':
                    try:
                        # Parse URL record structure
                        record_size = struct.unpack('<I', data[offset+4:offset+8])[0]
                        if record_size < 64 or record_size > len(data) - offset or record_size > 8192:
                            offset += 4
                            continue
                            
                        # Extract timestamps (Windows FILETIME format)
                        last_modified = struct.unpack('<Q', data[offset+8:offset+16])[0]
                        last_accessed = struct.unpack('<Q', data[offset+16:offset+24])[0]
                        
                        # Convert FILETIME to datetime
                        last_modified_dt = None
                        last_accessed_dt = None
                        
                        if last_modified > 0:
                            try:
                                last_modified_dt = datetime.fromtimestamp((last_modified - 116444736000000000) / 10000000)
                            except:
                                pass
                                
                        if last_accessed > 0:
                            try:
                                last_accessed_dt = datetime.fromtimestamp((last_accessed - 116444736000000000) / 10000000)
                            except:
                                pass
                        
                        # Extract URL string - it's typically after the fixed header
                        # Try different offsets to find the URL
                        url = ""
                        for url_offset in [52, 56, 60, 64]:
                            if url_offset < record_size:
                                try:
                                    # Look for null-terminated string
                                    url_start = offset + url_offset
                                    url_end = data.find(b'\x00', url_start, offset + record_size)
                                    if url_end == -1:
                                        url_end = offset + record_size
                                    
                                    potential_url = data[url_start:url_end].decode('ascii', errors='ignore')
                                    
                                    # Check if it looks like a URL
                                    if len(potential_url) > 3 and ('http' in potential_url.lower() or 
                                                                   'www.' in potential_url.lower() or
                                                                   '.' in potential_url):
                                        url = potential_url
                                        break
                                except:
                                    continue
                        
                        # If no proper URL found, try to extract any readable string
                        if not url:
                            try:
                                url_start = offset + 52
                                url_end = min(offset + record_size, url_start + 256)
                                potential_url = data[url_start:url_end].decode('ascii', errors='ignore')
                                # Clean up the string
                                url = ''.join(c for c in potential_url if c.isprintable()).split('\x00')[0]
                                if len(url) < 3:
                                    url = f"[Partial URL data at offset {offset}]"
                            except:
                                url = f"[Unable to parse URL at offset {offset}]"
                        
                        if url and len(url) > 1:
                            entries.append({
                                "source": "internet_explorer",
                                "url": url,
                                "last_modified": last_modified_dt.isoformat() if last_modified_dt else None,
                                "last_accessed": last_accessed_dt.isoformat() if last_accessed_dt else None,
                                "record_size": record_size
                            })
                        
                        offset += record_size
                    except Exception as e:
                        offset += 4
                else:
                    offset += 4
                    
        except Exception as e:
            print(f"Index.dat parsing error: {e}")
            
        return entries

    def extract_all_browser_artifacts(self, user_profiles):
        """Extract all browser artifacts for all user profiles"""
        all_artifacts = {
            "firefox": {"history": [], "cookies": [], "downloads": []},
            "chrome_edge": {"history": [], "cookies": [], "downloads": []},
            "internet_explorer": {"history": [], "cookies": []}
        }
        
        for profile in user_profiles:
            try:
                # Firefox artifacts
                firefox_artifacts = self.extract_firefox_artifacts(profile)
                all_artifacts["firefox"]["history"].extend(firefox_artifacts["history"])
                all_artifacts["firefox"]["cookies"].extend(firefox_artifacts["cookies"])
                all_artifacts["firefox"]["downloads"].extend(firefox_artifacts["downloads"])
                
                # Chrome/Edge artifacts
                chrome_edge_artifacts = self.extract_chrome_edge_artifacts(profile)
                all_artifacts["chrome_edge"]["history"].extend(chrome_edge_artifacts["history"])
                all_artifacts["chrome_edge"]["cookies"].extend(chrome_edge_artifacts["cookies"])
                all_artifacts["chrome_edge"]["downloads"].extend(chrome_edge_artifacts["downloads"])
                
                # Internet Explorer artifacts
                ie_artifacts = self.extract_ie_artifacts(profile)
                all_artifacts["internet_explorer"]["history"].extend(ie_artifacts["history"])
                all_artifacts["internet_explorer"]["cookies"].extend(ie_artifacts["cookies"])
                
            except Exception as e:
                print(f"Error extracting browser artifacts for {profile}: {e}")
                
        return all_artifacts