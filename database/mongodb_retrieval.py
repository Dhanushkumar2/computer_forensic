#!/usr/bin/env python3
"""
mongodb_retrieval.py
MongoDB retrieval module for querying forensic artifacts
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import yaml
from bson import ObjectId


class ForensicMongoRetrieval:
    def __init__(self, config_path="config/db_config.yaml"):
        """Initialize MongoDB connection"""
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        self.client = MongoClient(config["mongodb"]["uri"])
        self.db = self.client[config["mongodb"]["database"]]
        
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
            'user_activity': self.db.user_activity
        }
    
    def get_all_cases(self):
        """Get all cases"""
        return list(self.collections['cases'].find({}, {
            'case_id': 1, 
            'image_path': 1, 
            'extraction_time': 1, 
            'status': 1,
            'summary': 1
        }))
    
    def get_case_info(self, case_id):
        """Get detailed case information"""
        return self.collections['cases'].find_one({"case_id": case_id})
    
    def get_case_summary(self, case_id):
        """Get case summary statistics"""
        case = self.get_case_info(case_id)
        if not case:
            return None
        
        # Get counts from each collection
        summary = {
            "case_id": case_id,
            "image_path": case.get("image_path"),
            "extraction_time": case.get("extraction_time"),
            "user_profiles": case.get("user_profiles", []),
            "counts": {
                "browser_history": self.collections['browser_artifacts'].count_documents({
                    "case_id": case_id, "artifact_type": "browser_history"
                }),
                "browser_cookies": self.collections['browser_artifacts'].count_documents({
                    "case_id": case_id, "artifact_type": "browser_cookies"
                }),
                "browser_downloads": self.collections['browser_artifacts'].count_documents({
                    "case_id": case_id, "artifact_type": "browser_downloads"
                }),
                "usb_devices": self.collections['usb_devices'].count_documents({"case_id": case_id}),
                "user_activity": self.collections['user_activity'].count_documents({"case_id": case_id}),
                "installed_programs": self.collections['installed_programs'].count_documents({"case_id": case_id}),
                "event_logs": self.collections['event_log_artifacts'].count_documents({"case_id": case_id}),
                "filesystem_artifacts": self.collections['filesystem_artifacts'].count_documents({"case_id": case_id}),
                "deleted_files": self.collections['recycle_bin_artifacts'].count_documents({"case_id": case_id}),
                "timeline_events": self.collections['timeline_events'].count_documents({"case_id": case_id})
            }
        }
        
        return summary
    
    def get_browser_history(self, case_id, browser_type=None, limit=100):
        """Get browser history"""
        query = {"case_id": case_id, "artifact_type": "browser_history"}
        if browser_type:
            query["browser_type"] = browser_type
        
        return list(self.collections['browser_artifacts'].find(query)
                   .sort("timestamp", -1)
                   .limit(limit))
    
    def get_browser_cookies(self, case_id, browser_type=None, host=None, limit=100):
        """Get browser cookies"""
        query = {"case_id": case_id, "artifact_type": "browser_cookies"}
        if browser_type:
            query["browser_type"] = browser_type
        if host:
            query["host"] = {"$regex": host, "$options": "i"}
        
        return list(self.collections['browser_artifacts'].find(query)
                   .sort("timestamp", -1)
                   .limit(limit))
    
    def get_browser_downloads(self, case_id, browser_type=None, limit=100):
        """Get browser downloads"""
        query = {"case_id": case_id, "artifact_type": "browser_downloads"}
        if browser_type:
            query["browser_type"] = browser_type
        
        return list(self.collections['browser_artifacts'].find(query)
                   .sort("timestamp", -1)
                   .limit(limit))
    
    def get_usb_devices(self, case_id):
        """Get USB device history"""
        return list(self.collections['usb_devices'].find({"case_id": case_id})
                   .sort("first_install", -1))
    
    def get_user_activity(self, case_id, activity_type=None, limit=100):
        """Get user activity (UserAssist data)"""
        query = {"case_id": case_id}
        if activity_type:
            query["activity_type"] = activity_type
        
        return list(self.collections['user_activity'].find(query)
                   .sort("last_run", -1)
                   .limit(limit))
    
    def get_most_executed_programs(self, case_id, limit=20):
        """Get most frequently executed programs"""
        return list(self.collections['user_activity'].find({"case_id": case_id})
                   .sort("run_count", -1)
                   .limit(limit))
    
    def get_installed_programs(self, case_id, publisher=None):
        """Get installed programs"""
        query = {"case_id": case_id}
        if publisher:
            query["publisher"] = {"$regex": publisher, "$options": "i"}
        
        return list(self.collections['installed_programs'].find(query)
                   .sort("display_name", 1))
    
    def get_run_keys(self, case_id):
        """Get persistence mechanisms (run keys)"""
        return list(self.collections['registry_artifacts'].find({
            "case_id": case_id,
            "artifact_type": "run_key"
        }))
    
    def get_system_info(self, case_id):
        """Get system information"""
        system_info = {}
        
        # Get last logged user
        last_user = self.collections['registry_artifacts'].find_one({
            "case_id": case_id,
            "artifact_type": "last_logged_user"
        })
        if last_user:
            system_info["last_logged_user"] = last_user.get("data", {})
        
        # Get timezone info
        timezone = self.collections['registry_artifacts'].find_one({
            "case_id": case_id,
            "artifact_type": "timezone_info"
        })
        if timezone:
            system_info["timezone_info"] = timezone.get("data", {})
        
        # Get network info
        network = self.collections['registry_artifacts'].find_one({
            "case_id": case_id,
            "artifact_type": "network_info"
        })
        if network:
            system_info["network_info"] = network.get("data", {})
        
        return system_info
    
    def get_event_logs(self, case_id, event_type=None, source_name=None, limit=100):
        """Get event log entries"""
        query = {"case_id": case_id}
        if event_type:
            query["event_type"] = event_type
        if source_name:
            query["source_name"] = {"$regex": source_name, "$options": "i"}
        
        return list(self.collections['event_log_artifacts'].find(query)
                   .sort("time_generated", -1)
                   .limit(limit))
    
    def get_logon_events(self, case_id):
        """Get logon-related events"""
        logon_event_ids = [528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 
                          4624, 4625, 4634, 4647, 4648]
        
        return list(self.collections['event_log_artifacts'].find({
            "case_id": case_id,
            "event_id": {"$in": logon_event_ids}
        }).sort("time_generated", -1))
    
    def get_filesystem_artifacts(self, case_id, artifact_type=None, limit=100):
        """Get filesystem artifacts"""
        query = {"case_id": case_id}
        if artifact_type:
            query["artifact_type"] = artifact_type
        
        return list(self.collections['filesystem_artifacts'].find(query)
                   .sort("timestamp", -1)
                   .limit(limit))
    
    def get_prefetch_files(self, case_id):
        """Get prefetch files"""
        return list(self.collections['filesystem_artifacts'].find({
            "case_id": case_id,
            "artifact_type": "prefetch"
        }).sort("last_run_time", -1))
    
    def get_link_files(self, case_id, target_contains=None):
        """Get link files"""
        query = {"case_id": case_id, "artifact_type": "link_file"}
        if target_contains:
            query["target_path"] = {"$regex": target_contains, "$options": "i"}
        
        return list(self.collections['filesystem_artifacts'].find(query)
                   .sort("creation_time", -1))
    
    def get_deleted_files(self, case_id, filename_contains=None):
        """Get deleted files from recycle bin"""
        query = {"case_id": case_id}
        if filename_contains:
            query["original_filename"] = {"$regex": filename_contains, "$options": "i"}
        
        return list(self.collections['recycle_bin_artifacts'].find(query)
                   .sort("deletion_time", -1))
    
    def get_timeline(self, case_id, start_date=None, end_date=None, event_type=None, limit=200):
        """Get timeline events"""
        query = {"case_id": case_id}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["timestamp"] = date_query
        
        if event_type:
            query["event_type"] = event_type
        
        return list(self.collections['timeline_events'].find(query)
                   .sort("timestamp", -1)
                   .limit(limit))
    
    def search_artifacts(self, case_id, search_term, collections=None):
        """Search across multiple artifact types"""
        if collections is None:
            collections = ['browser_artifacts', 'user_activity', 'installed_programs', 
                          'filesystem_artifacts', 'recycle_bin_artifacts']
        
        results = {}
        
        # Search browser artifacts
        if 'browser_artifacts' in collections:
            results['browser_artifacts'] = list(self.collections['browser_artifacts'].find({
                "case_id": case_id,
                "$or": [
                    {"url": {"$regex": search_term, "$options": "i"}},
                    {"title": {"$regex": search_term, "$options": "i"}},
                    {"name": {"$regex": search_term, "$options": "i"}},
                    {"host": {"$regex": search_term, "$options": "i"}}
                ]
            }).limit(50))
        
        # Search user activity
        if 'user_activity' in collections:
            results['user_activity'] = list(self.collections['user_activity'].find({
                "case_id": case_id,
                "program_name": {"$regex": search_term, "$options": "i"}
            }).limit(50))
        
        # Search installed programs
        if 'installed_programs' in collections:
            results['installed_programs'] = list(self.collections['installed_programs'].find({
                "case_id": case_id,
                "$or": [
                    {"display_name": {"$regex": search_term, "$options": "i"}},
                    {"publisher": {"$regex": search_term, "$options": "i"}}
                ]
            }).limit(50))
        
        # Search filesystem artifacts
        if 'filesystem_artifacts' in collections:
            results['filesystem_artifacts'] = list(self.collections['filesystem_artifacts'].find({
                "case_id": case_id,
                "$or": [
                    {"filename": {"$regex": search_term, "$options": "i"}},
                    {"executable_name": {"$regex": search_term, "$options": "i"}},
                    {"target_path": {"$regex": search_term, "$options": "i"}}
                ]
            }).limit(50))
        
        # Search deleted files
        if 'recycle_bin_artifacts' in collections:
            results['recycle_bin_artifacts'] = list(self.collections['recycle_bin_artifacts'].find({
                "case_id": case_id,
                "original_filename": {"$regex": search_term, "$options": "i"}
            }).limit(50))
        
        return results
    
    def get_activity_by_date_range(self, case_id, start_date, end_date):
        """Get all activity within a date range"""
        date_query = {"$gte": start_date, "$lte": end_date}
        
        results = {
            "browser_history": list(self.collections['browser_artifacts'].find({
                "case_id": case_id,
                "artifact_type": "browser_history",
                "timestamp": date_query
            }).sort("timestamp", -1)),
            
            "user_activity": list(self.collections['user_activity'].find({
                "case_id": case_id,
                "timestamp": date_query
            }).sort("timestamp", -1)),
            
            "usb_devices": list(self.collections['usb_devices'].find({
                "case_id": case_id,
                "timestamp": date_query
            }).sort("timestamp", -1)),
            
            "deleted_files": list(self.collections['recycle_bin_artifacts'].find({
                "case_id": case_id,
                "timestamp": date_query
            }).sort("timestamp", -1)),
            
            "timeline_events": list(self.collections['timeline_events'].find({
                "case_id": case_id,
                "timestamp": date_query
            }).sort("timestamp", -1))
        }
        
        return results
    
    def get_user_profile_activity(self, case_id, user_profile):
        """Get activity for specific user profile"""
        # This would require storing user profile info with artifacts
        # For now, return general activity that might be user-specific
        return {
            "user_activity": list(self.collections['user_activity'].find({
                "case_id": case_id
            }).sort("last_run", -1)),
            
            "browser_artifacts": list(self.collections['browser_artifacts'].find({
                "case_id": case_id
            }).sort("timestamp", -1).limit(100))
        }
    
    def get_statistics(self, case_id):
        """Get comprehensive statistics for a case"""
        stats = {}
        
        # Browser statistics
        browser_stats = list(self.collections['browser_artifacts'].aggregate([
            {"$match": {"case_id": case_id}},
            {"$group": {
                "_id": {"artifact_type": "$artifact_type", "browser_type": "$browser_type"},
                "count": {"$sum": 1}
            }}
        ]))
        stats["browser_stats"] = browser_stats
        
        # Most visited domains
        top_domains = list(self.collections['browser_artifacts'].aggregate([
            {"$match": {"case_id": case_id, "artifact_type": "browser_history"}},
            {"$group": {
                "_id": "$host",
                "visit_count": {"$sum": "$visit_count"},
                "total_visits": {"$sum": 1}
            }},
            {"$sort": {"visit_count": -1}},
            {"$limit": 10}
        ]))
        stats["top_domains"] = top_domains
        
        # Activity by hour
        activity_by_hour = list(self.collections['timeline_events'].aggregate([
            {"$match": {"case_id": case_id}},
            {"$group": {
                "_id": {"$hour": {"$dateFromString": {"dateString": "$timestamp"}}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]))
        stats["activity_by_hour"] = activity_by_hour
        
        # USB device manufacturers
        usb_manufacturers = list(self.collections['usb_devices'].aggregate([
            {"$match": {"case_id": case_id}},
            {"$group": {
                "_id": {"$arrayElemAt": [{"$split": ["$device_name", "&"]}, 1]},
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]))
        stats["usb_manufacturers"] = usb_manufacturers
        
        return stats
    
    def close(self):
        """Close database connection"""
        self.client.close()


if __name__ == "__main__":
    # Example usage
    retrieval = ForensicMongoRetrieval()
    
    try:
        # List all cases
        cases = retrieval.get_all_cases()
        print("Available cases:")
        for case in cases:
            print(f"  - {case['case_id']}: {case['image_path']}")
        
        if cases:
            case_id = cases[0]['case_id']
            print(f"\nAnalyzing case: {case_id}")
            
            # Get case summary
            summary = retrieval.get_case_summary(case_id)
            print(f"Summary: {summary}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        retrieval.close()