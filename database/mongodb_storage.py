#!/usr/bin/env python3
"""
mongodb_storage.py
MongoDB storage module for forensic artifacts
"""

import json
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
from bson import ObjectId
import yaml


class ForensicMongoStorage:
    def __init__(self, config_path="config/db_config.yaml"):
        """Initialize MongoDB connection"""
        config = None
        config_path = Path(config_path)
        if not config_path.is_file():
            fallback = Path(__file__).resolve().parent.parent / "config" / "db_config.yaml"
            if fallback.is_file():
                config_path = fallback
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except Exception:
            config = {"mongodb": {"host": "localhost", "port": 27017, "database": "forensic_ir"}}

        mongo_config = config["mongodb"]
        mongo_uri = mongo_config.get("uri")
        if not mongo_uri:
            mongo_host = mongo_config.get("host", "localhost")
            mongo_port = mongo_config.get("port", 27017)
            mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/"

        mongo_database = mongo_config.get("database", "forensics")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[mongo_database]
        
        # Define collections
        self.collections = {
            'cases': self.db.cases,
            'browser_artifacts': self.db.browser_artifacts,
            'registry_artifacts': self.db.registry_artifacts,
            'recycle_bin_artifacts': self.db.recycle_bin_artifacts,
            'event_log_artifacts': self.db.event_log_artifacts,
            'filesystem_artifacts': self.db.filesystem_artifacts,
            'timeline_events': self.db.timeline_events,
            'usb_devices': self.db.usb_devices,
            'installed_programs': self.db.installed_programs,
            'user_activity': self.db.user_activity,
            'android_artifacts': self.db.android_artifacts,
            'ml_anomalies': self.db.ml_anomalies,
            'android_ml_anomalies': self.db.android_ml_anomalies
        }
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better query performance"""
        try:
            # Case indexes
            self.collections['cases'].create_index("case_id", unique=True)
            self.collections['cases'].create_index("image_path")
            
            # Browser artifacts indexes
            self.collections['browser_artifacts'].create_index([("case_id", 1), ("browser_type", 1)])
            self.collections['browser_artifacts'].create_index("url")
            self.collections['browser_artifacts'].create_index("timestamp")
            
            # Registry artifacts indexes
            self.collections['registry_artifacts'].create_index([("case_id", 1), ("artifact_type", 1)])
            self.collections['registry_artifacts'].create_index("device_name")
            self.collections['registry_artifacts'].create_index("program_name")
            
            # Timeline indexes
            self.collections['timeline_events'].create_index([("case_id", 1), ("timestamp", 1)])
            self.collections['timeline_events'].create_index("event_type")
            
            # USB devices indexes
            self.collections['usb_devices'].create_index([("case_id", 1), ("device_name", 1)])
            self.collections['usb_devices'].create_index("first_install")
            
            # User activity indexes
            self.collections['user_activity'].create_index([("case_id", 1), ("user_profile", 1)])
            self.collections['user_activity'].create_index("program_name")
            self.collections['user_activity'].create_index("last_run")

            # Android artifacts indexes
            self.collections['android_artifacts'].create_index([("case_id", 1), ("artifact_type", 1)])
            self.collections['android_artifacts'].create_index("package_name")
            self.collections['android_artifacts'].create_index("path")

            # ML anomalies indexes
            self.collections['ml_anomalies'].create_index([("case_id", 1), ("anomaly_score", -1)])
            self.collections['ml_anomalies'].create_index("label")

            # Android ML anomalies indexes
            self.collections['android_ml_anomalies'].create_index([("case_id", 1), ("anomaly_score", -1)])
            self.collections['android_ml_anomalies'].create_index("label")
            
        except Exception as e:
            print(f"Warning: Could not create some indexes: {e}")

    def delete_case_artifacts(self, case_id):
        """Delete all artifacts for a case to avoid duplication."""
        for name, collection in self.collections.items():
            if name == 'cases':
                continue
            collection.delete_many({"case_id": case_id})
    
    def store_case_info(self, case_data):
        """Store case information"""
        case_id = case_data.get("case_id", self._generate_case_id())
        extraction_info = case_data.get("extraction_info", {})
        case_doc = {
            "case_id": case_id,
            "image_path": extraction_info.get("image_path"),
            "extraction_time": extraction_info.get("extraction_time"),
            "ntfs_offset": extraction_info.get("ntfs_offset"),
            "user_profiles": extraction_info.get("user_profiles", []),
            "format": extraction_info.get("format"),
            "summary": case_data.get("summary", {}),
            "updated_at": datetime.now().isoformat(),
            "status": "processed"
        }

        result = self.collections['cases'].update_one(
            {"case_id": case_id},
            {"$set": case_doc, "$setOnInsert": {"created_at": datetime.now().isoformat()}},
            upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else None, case_id

    def store_android_artifacts(self, case_id, android_data):
        """Store Android TAR artifacts"""
        documents = []

        for package in android_data.get("android_packages", []):
            documents.append({
                "case_id": case_id,
                "artifact_type": "package",
                "package_name": package,
                "created_at": datetime.now().isoformat(),
            })

        def _add_files(items, artifact_type):
            for item in items:
                documents.append({
                    "case_id": case_id,
                    "artifact_type": artifact_type,
                    "path": item.get("path"),
                    "size": item.get("size"),
                    "mtime": item.get("mtime"),
                    "file_type": item.get("type"),
                    "package_name": item.get("package_name"),
                    "created_at": datetime.now().isoformat(),
                })

        _add_files(android_data.get("manifests", []), "manifest")
        _add_files(android_data.get("app_databases", []), "app_database")
        _add_files(android_data.get("shared_preferences", []), "shared_pref")
        _add_files(android_data.get("webview_artifacts", []), "webview")
        _add_files(android_data.get("calendar_databases", []), "calendar_db")
        _add_files(android_data.get("sms_backups", []), "sms_backup")
        _add_files(android_data.get("other_app_artifacts", []), "other_app_file")

        if documents:
            result = self.collections['android_artifacts'].insert_many(documents)
            return len(result.inserted_ids)
        return 0

    def store_ml_anomalies(self, case_id, items, summary=None):
        """Store ML inference results (top anomalies)."""
        if case_id:
            self.collections['ml_anomalies'].delete_many({"case_id": case_id})

        documents = []
        for item in items or []:
            doc = {"case_id": case_id, "created_at": datetime.now().isoformat()}
            doc.update(item)
            documents.append(doc)

        inserted = 0
        if documents:
            result = self.collections['ml_anomalies'].insert_many(documents)
            inserted = len(result.inserted_ids)

        if summary and case_id:
            self.collections['cases'].update_one(
                {"case_id": case_id},
                {"$set": {"ml_inference": summary}}
            )

        return inserted

    def store_android_ml_anomalies(self, case_id, items, summary=None):
        """Store Android ML inference results."""
        if case_id:
            self.collections['android_ml_anomalies'].delete_many({"case_id": case_id})

        documents = []
        for item in items or []:
            doc = {"case_id": case_id, "created_at": datetime.now().isoformat()}
            doc.update(item)
            documents.append(doc)

        inserted = 0
        if documents:
            result = self.collections['android_ml_anomalies'].insert_many(documents)
            inserted = len(result.inserted_ids)

        if summary and case_id:
            self.collections['cases'].update_one(
                {"case_id": case_id},
                {"$set": {"android_ml_inference": summary}}
            )

        return inserted

    def upsert_case_record(self, case_id, case_details, summary=None, raw_file_info=None, status="created"):
        """Create or update a case record in MongoDB."""
        now = datetime.now().isoformat()
        update_doc = {
            "case_id": case_id,
            "status": status,
            "case_details": case_details or {},
            "updated_at": now,
        }
        if summary is not None:
            update_doc["summary"] = summary
        if raw_file_info is not None:
            update_doc["raw_file"] = raw_file_info

        result = self.collections['cases'].update_one(
            {"case_id": case_id},
            {
                "$set": update_doc,
                "$setOnInsert": {"created_at": now},
            },
            upsert=True
        )

        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None,
        }
    
    def store_browser_artifacts(self, case_id, browser_data):
        """Store browser artifacts"""
        documents = []
        
        for browser_type, artifacts in browser_data.items():
            # Store history
            for entry in artifacts.get("history", []):
                doc = {
                    "case_id": case_id,
                    "artifact_type": "browser_history",
                    "browser_type": browser_type,
                    "url": entry.get("url"),
                    "title": entry.get("title"),
                    "visit_count": entry.get("visit_count", 0),
                    "last_visit": entry.get("last_visit"),
                    "timestamp": entry.get("last_visit"),
                    "typed_count": entry.get("typed_count", 0),
                    "created_at": datetime.now().isoformat()
                }
                documents.append(doc)
            
            # Store cookies
            for entry in artifacts.get("cookies", []):
                doc = {
                    "case_id": case_id,
                    "artifact_type": "browser_cookies",
                    "browser_type": browser_type,
                    "name": entry.get("name"),
                    "value": entry.get("value"),
                    "host": entry.get("host"),
                    "path": entry.get("path"),
                    "expires": entry.get("expires"),
                    "last_access": entry.get("last_access"),
                    "timestamp": entry.get("last_access"),
                    "is_secure": entry.get("is_secure", False),
                    "is_httponly": entry.get("is_httponly", False),
                    "created_at": datetime.now().isoformat()
                }
                documents.append(doc)
            
            # Store downloads
            for entry in artifacts.get("downloads", []):
                doc = {
                    "case_id": case_id,
                    "artifact_type": "browser_downloads",
                    "browser_type": browser_type,
                    "url": entry.get("url"),
                    "target_path": entry.get("target_path"),
                    "current_path": entry.get("current_path"),
                    "start_time": entry.get("start_time"),
                    "end_time": entry.get("end_time"),
                    "timestamp": entry.get("start_time"),
                    "received_bytes": entry.get("received_bytes", 0),
                    "total_bytes": entry.get("total_bytes", 0),
                    "state": entry.get("state"),
                    "created_at": datetime.now().isoformat()
                }
                documents.append(doc)
        
        if documents:
            result = self.collections['browser_artifacts'].insert_many(documents)
            return len(result.inserted_ids)
        return 0
    
    def store_usb_devices(self, case_id, usb_data):
        """Store USB device history"""
        documents = []
        
        for device in usb_data:
            doc = {
                "case_id": case_id,
                "device_class": device.get("device_class"),
                "device_name": device.get("device_name"),
                "instance_id": device.get("instance_id"),
                "friendly_name": device.get("friendly_name"),
                "first_install": device.get("first_install"),
                "last_arrival": device.get("last_arrival"),
                "last_removal": device.get("last_removal"),
                "timestamp": device.get("first_install"),
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        if documents:
            result = self.collections['usb_devices'].insert_many(documents)
            return len(result.inserted_ids)
        return 0
    
    def store_user_activity(self, case_id, userassist_data):
        """Store UserAssist (user activity) data"""
        documents = []
        
        for entry in userassist_data:
            # Clean up program name
            program = entry.get("program", "")
            if "UEME_RUNPIDL:" in program:
                program_name = program.replace("UEME_RUNPIDL:", "")
                activity_type = "shortcut_execution"
            elif "UEME_RUNPATH:" in program:
                program_name = program.replace("UEME_RUNPATH:", "")
                activity_type = "program_execution"
            else:
                program_name = program
                activity_type = "system_activity"
            
            doc = {
                "case_id": case_id,
                "guid": entry.get("guid"),
                "program_name": program_name,
                "original_program": program,
                "activity_type": activity_type,
                "run_count": entry.get("run_count", 0),
                "last_run": entry.get("last_run"),
                "timestamp": entry.get("last_run"),
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        if documents:
            result = self.collections['user_activity'].insert_many(documents)
            return len(result.inserted_ids)
        return 0
    
    def store_installed_programs(self, case_id, programs_data):
        """Store installed programs"""
        documents = []
        
        for program in programs_data:
            doc = {
                "case_id": case_id,
                "registry_key": program.get("registry_key"),
                "display_name": program.get("display_name"),
                "display_version": program.get("display_version"),
                "publisher": program.get("publisher"),
                "install_date": program.get("install_date"),
                "install_location": program.get("install_location"),
                "uninstall_string": program.get("uninstall_string"),
                "estimated_size": program.get("estimated_size", 0),
                "timestamp": program.get("install_date"),
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        if documents:
            result = self.collections['installed_programs'].insert_many(documents)
            return len(result.inserted_ids)
        return 0
    
    def store_registry_artifacts(self, case_id, registry_data):
        """Store other registry artifacts"""
        documents = []
        
        # Store run keys
        for run_key in registry_data.get("run_keys", []):
            doc = {
                "case_id": case_id,
                "artifact_type": "run_key",
                "hive": run_key.get("hive"),
                "key_path": run_key.get("key_path"),
                "name": run_key.get("name"),
                "value": run_key.get("value"),
                "type": run_key.get("type"),
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        # Store system info
        if registry_data.get("last_logged_user"):
            doc = {
                "case_id": case_id,
                "artifact_type": "last_logged_user",
                "data": registry_data["last_logged_user"],
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        if registry_data.get("timezone_info"):
            doc = {
                "case_id": case_id,
                "artifact_type": "timezone_info",
                "data": registry_data["timezone_info"],
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        if registry_data.get("network_info"):
            doc = {
                "case_id": case_id,
                "artifact_type": "network_info",
                "data": registry_data["network_info"],
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        if documents:
            result = self.collections['registry_artifacts'].insert_many(documents)
            return len(result.inserted_ids)
        return 0
    
    def store_event_logs(self, case_id, event_data):
        """Store event log artifacts"""
        documents = []
        
        for event in event_data.get("all_events", []):
            doc = {
                "case_id": case_id,
                "record_number": event.get("record_number"),
                "event_id": event.get("event_id"),
                "event_type": event.get("event_type"),
                "event_category": event.get("event_category"),
                "time_generated": event.get("time_generated"),
                "time_written": event.get("time_written"),
                "timestamp": event.get("time_generated"),
                "source_name": event.get("source_name"),
                "computer_name": event.get("computer_name"),
                "strings": event.get("strings", []),
                "user_sid_length": event.get("user_sid_length", 0),
                "data_length": event.get("data_length", 0),
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        if documents:
            result = self.collections['event_log_artifacts'].insert_many(documents)
            return len(result.inserted_ids)
        return 0
    
    def store_filesystem_artifacts(self, case_id, fs_data):
        """Store filesystem artifacts"""
        documents = []
        
        # Store prefetch files
        for pf in fs_data.get("prefetch_files", []):
            doc = {
                "case_id": case_id,
                "artifact_type": "prefetch",
                "filename": pf.get("filename"),
                "executable_name": pf.get("executable_name"),
                "run_count": pf.get("run_count", 0),
                "last_run_time": pf.get("last_run_time"),
                "timestamp": pf.get("last_run_time"),
                "version": pf.get("version"),
                "prefetch_hash": pf.get("prefetch_hash"),
                "file_path": pf.get("file_path"),
                "file_size": pf.get("file_size", 0),
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        # Store link files
        for link in fs_data.get("link_files", []):
            doc = {
                "case_id": case_id,
                "artifact_type": "link_file",
                "filename": link.get("filename"),
                "target_path": link.get("target_path"),
                "arguments": link.get("arguments"),
                "working_directory": link.get("working_directory"),
                "creation_time": link.get("creation_time"),
                "access_time": link.get("access_time"),
                "write_time": link.get("write_time"),
                "timestamp": link.get("creation_time"),
                "file_size": link.get("file_size", 0),
                "file_path": link.get("file_path"),
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        # Store jump lists
        for jl in fs_data.get("jump_lists", []):
            doc = {
                "case_id": case_id,
                "artifact_type": "jump_list",
                "filename": jl.get("filename"),
                "path": jl.get("path"),
                "size": jl.get("size", 0),
                "created": jl.get("created"),
                "modified": jl.get("modified"),
                "timestamp": jl.get("modified"),
                "type": jl.get("type"),
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        if documents:
            result = self.collections['filesystem_artifacts'].insert_many(documents)
            return len(result.inserted_ids)
        return 0
    
    def store_recycle_bin_artifacts(self, case_id, recycle_data):
        """Store recycle bin artifacts"""
        documents = []
        
        for deleted_file in recycle_data.get("deleted_files", []):
            doc = {
                "case_id": case_id,
                "original_filename": deleted_file.get("original_filename"),
                "recycle_filename": deleted_file.get("recycle_filename"),
                "deletion_time": deleted_file.get("deletion_time"),
                "timestamp": deleted_file.get("deletion_time"),
                "file_size": deleted_file.get("file_size", 0),
                "drive_number": deleted_file.get("drive_number"),
                "drive_letter": deleted_file.get("drive_letter"),
                "record_number": deleted_file.get("record_number"),
                "user_sid": deleted_file.get("user_sid"),
                "created_at": datetime.now().isoformat()
            }
            documents.append(doc)
        
        if documents:
            result = self.collections['recycle_bin_artifacts'].insert_many(documents)
            return len(result.inserted_ids)
        return 0
    
    def create_timeline_events(self, case_id):
        """Create unified timeline from all artifacts"""
        timeline_events = []
        
        # Get USB device events
        usb_devices = self.collections['usb_devices'].find({"case_id": case_id})
        for device in usb_devices:
            if device.get("first_install"):
                timeline_events.append({
                    "case_id": case_id,
                    "timestamp": device["first_install"],
                    "event_type": "USB Device Connected",
                    "description": f"USB device connected: {device.get('friendly_name', device.get('device_name'))}",
                    "source": "usb_devices",
                    "source_id": str(device["_id"]),
                    "created_at": datetime.now().isoformat()
                })
        
        # Get user activity events
        user_activities = self.collections['user_activity'].find({"case_id": case_id})
        for activity in user_activities:
            if activity.get("last_run"):
                timeline_events.append({
                    "case_id": case_id,
                    "timestamp": activity["last_run"],
                    "event_type": "Program Execution",
                    "description": f"Program executed: {activity.get('program_name')}",
                    "source": "user_activity",
                    "source_id": str(activity["_id"]),
                    "created_at": datetime.now().isoformat()
                })
        
        # Get browser history events
        browser_history = self.collections['browser_artifacts'].find({
            "case_id": case_id, 
            "artifact_type": "browser_history"
        })
        for entry in browser_history:
            if entry.get("last_visit"):
                timeline_events.append({
                    "case_id": case_id,
                    "timestamp": entry["last_visit"],
                    "event_type": "Web Browsing",
                    "description": f"Visited: {entry.get('url')} ({entry.get('browser_type')})",
                    "source": "browser_artifacts",
                    "source_id": str(entry["_id"]),
                    "created_at": datetime.now().isoformat()
                })
        
        # Get file deletion events
        deleted_files = self.collections['recycle_bin_artifacts'].find({"case_id": case_id})
        for file_entry in deleted_files:
            if file_entry.get("deletion_time"):
                timeline_events.append({
                    "case_id": case_id,
                    "timestamp": file_entry["deletion_time"],
                    "event_type": "File Deleted",
                    "description": f"File deleted: {file_entry.get('original_filename')}",
                    "source": "recycle_bin_artifacts",
                    "source_id": str(file_entry["_id"]),
                    "created_at": datetime.now().isoformat()
                })
        
        # Store timeline events
        if timeline_events:
            result = self.collections['timeline_events'].insert_many(timeline_events)
            return len(result.inserted_ids)
        return 0
    
    def store_all_artifacts(self, json_file_path):
        """Store all artifacts from JSON file"""
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        print("Storing forensic artifacts in MongoDB...")

        # Clean existing artifacts for this case to avoid duplicates.
        case_id = data.get("case_id")
        if case_id:
            self.delete_case_artifacts(case_id)
        
        # Store case info
        case_object_id, case_id = self.store_case_info(data)
        print(f"✓ Case stored with ID: {case_id}")

        is_android = "android_packages" in data or data.get("extraction_info", {}).get("format") == "android_tar"
        if is_android:
            android_count = self.store_android_artifacts(case_id, data)
            print(f"✓ Android artifacts stored: {android_count}")
            print(f"\n🎉 All Android artifacts stored successfully for case: {case_id}")
            return case_id
        
        # Store browser artifacts
        browser_count = self.store_browser_artifacts(case_id, data["browser_artifacts"])
        print(f"✓ Browser artifacts stored: {browser_count}")
        
        # Store USB devices
        usb_count = self.store_usb_devices(case_id, data["registry_artifacts"]["usb_history"])
        print(f"✓ USB devices stored: {usb_count}")
        
        # Store user activity
        activity_count = self.store_user_activity(case_id, data["registry_artifacts"]["userassist"])
        print(f"✓ User activity records stored: {activity_count}")
        
        # Store installed programs
        programs_count = self.store_installed_programs(case_id, data["registry_artifacts"]["installed_programs"])
        print(f"✓ Installed programs stored: {programs_count}")
        
        # Store other registry artifacts
        registry_count = self.store_registry_artifacts(case_id, data["registry_artifacts"])
        print(f"✓ Registry artifacts stored: {registry_count}")
        
        # Store event logs
        events_count = self.store_event_logs(case_id, data["event_log_artifacts"])
        print(f"✓ Event log entries stored: {events_count}")
        
        # Store filesystem artifacts
        fs_count = self.store_filesystem_artifacts(case_id, data["filesystem_artifacts"])
        print(f"✓ Filesystem artifacts stored: {fs_count}")
        
        # Store recycle bin artifacts
        recycle_count = self.store_recycle_bin_artifacts(case_id, data["recycle_bin_artifacts"])
        print(f"✓ Recycle bin artifacts stored: {recycle_count}")
        
        # Create timeline
        timeline_count = self.create_timeline_events(case_id)
        print(f"✓ Timeline events created: {timeline_count}")
        
        print(f"\n🎉 All artifacts stored successfully for case: {case_id}")
        return case_id
    
    def _generate_case_id(self):
        """Generate unique case ID"""
        return f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def close(self):
        """Close database connection"""
        self.client.close()


if __name__ == "__main__":
    import sys
    
    json_file = sys.argv[1] if len(sys.argv) > 1 else "test_comprehensive_artifacts.json"
    
    storage = ForensicMongoStorage()
    
    try:
        case_id = storage.store_all_artifacts(json_file)
        print(f"\nCase ID for future reference: {case_id}")
    except Exception as e:
        print(f"Error storing artifacts: {e}")
    finally:
        storage.close()
