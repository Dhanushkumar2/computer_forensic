"""
MongoDB service layer for forensic API
"""
import sys
import os
from datetime import datetime, timedelta
from django.conf import settings

# Add parent directories to path to import our MongoDB modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.mongodb_retrieval import ForensicMongoRetrieval
from database.mongodb_storage import ForensicMongoStorage


class ForensicMongoService:
    """Service layer for MongoDB operations"""
    
    def __init__(self):
        self.retrieval = ForensicMongoRetrieval()
        self.storage = ForensicMongoStorage()
    
    def close(self):
        """Close MongoDB connections"""
        self.retrieval.close()
        self.storage.close()
    
    # Case operations
    def get_case_summary(self, case_id):
        """Get case summary"""
        return self.retrieval.get_case_summary(case_id)
    
    def get_case_statistics(self, case_id):
        """Get case statistics"""
        return self.retrieval.get_statistics(case_id)
    
    # Browser artifacts
    def get_browser_history(self, case_id, browser_type=None, limit=100, offset=0):
        """Get browser history with pagination"""
        history = self.retrieval.get_browser_history(case_id, browser_type, limit + offset)
        return history[offset:offset + limit] if history else []
    
    def get_browser_cookies(self, case_id, browser_type=None, host=None, limit=100, offset=0):
        """Get browser cookies with pagination"""
        cookies = self.retrieval.get_browser_cookies(case_id, browser_type, host, limit + offset)
        return cookies[offset:offset + limit] if cookies else []
    
    def get_browser_downloads(self, case_id, browser_type=None, limit=100, offset=0):
        """Get browser downloads with pagination"""
        downloads = self.retrieval.get_browser_downloads(case_id, browser_type, limit + offset)
        return downloads[offset:offset + limit] if downloads else []
    
    # USB devices
    def get_usb_devices(self, case_id):
        """Get USB devices"""
        return self.retrieval.get_usb_devices(case_id)
    
    # User activity
    def get_user_activity(self, case_id, activity_type=None, limit=100, offset=0):
        """Get user activity with pagination"""
        activity = self.retrieval.get_user_activity(case_id, activity_type, limit + offset)
        return activity[offset:offset + limit] if activity else []
    
    def get_most_executed_programs(self, case_id, limit=20):
        """Get most executed programs"""
        return self.retrieval.get_most_executed_programs(case_id, limit)
    
    # Installed programs
    def get_installed_programs(self, case_id, publisher=None):
        """Get installed programs"""
        return self.retrieval.get_installed_programs(case_id, publisher)
    
    # Registry artifacts
    def get_run_keys(self, case_id):
        """Get run keys"""
        return self.retrieval.get_run_keys(case_id)
    
    def get_system_info(self, case_id):
        """Get system information"""
        return self.retrieval.get_system_info(case_id)
    
    # Event logs
    def get_event_logs(self, case_id, event_type=None, source_name=None, limit=100, offset=0):
        """Get event logs with pagination"""
        events = self.retrieval.get_event_logs(case_id, event_type, source_name, limit + offset)
        return events[offset:offset + limit] if events else []
    
    def get_logon_events(self, case_id):
        """Get logon events"""
        return self.retrieval.get_logon_events(case_id)
    
    # Filesystem artifacts
    def get_filesystem_artifacts(self, case_id, artifact_type=None, limit=100, offset=0):
        """Get filesystem artifacts with pagination"""
        artifacts = self.retrieval.get_filesystem_artifacts(case_id, artifact_type, limit + offset)
        return artifacts[offset:offset + limit] if artifacts else []
    
    def get_prefetch_files(self, case_id):
        """Get prefetch files"""
        return self.retrieval.get_prefetch_files(case_id)
    
    def get_link_files(self, case_id, target_contains=None):
        """Get link files"""
        return self.retrieval.get_link_files(case_id, target_contains)
    
    # Deleted files
    def get_deleted_files(self, case_id, filename_contains=None):
        """Get deleted files"""
        return self.retrieval.get_deleted_files(case_id, filename_contains)
    
    # Timeline
    def get_timeline(self, case_id, start_date=None, end_date=None, event_type=None, limit=200, offset=0):
        """Get timeline with pagination"""
        timeline = self.retrieval.get_timeline(case_id, start_date, end_date, event_type, limit + offset)
        return timeline[offset:offset + limit] if timeline else []
    
    # Search
    def search_artifacts(self, case_id, search_term, collections=None):
        """Search across artifacts"""
        return self.retrieval.search_artifacts(case_id, search_term, collections)
    
    def get_activity_by_date_range(self, case_id, start_date, end_date):
        """Get activity by date range"""
        return self.retrieval.get_activity_by_date_range(case_id, start_date, end_date)
    
    # Advanced queries
    def get_suspicious_activity(self, case_id):
        """Get potentially suspicious activity"""
        suspicious_indicators = []
        
        # Check for deleted executable files
        deleted_files = self.get_deleted_files(case_id)
        suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        suspicious_deletions = []
        
        for file_entry in deleted_files:
            filename = file_entry.get('original_filename', '').lower()
            if any(filename.endswith(ext) for ext in suspicious_extensions):
                suspicious_deletions.append(file_entry)
        
        if suspicious_deletions:
            suspicious_indicators.append({
                'type': 'deleted_executables',
                'count': len(suspicious_deletions),
                'description': f'Deleted executable files: {len(suspicious_deletions)}',
                'items': suspicious_deletions[:10]  # Limit to first 10
            })
        
        # Check for late-night activity
        user_activity = self.get_user_activity(case_id, limit=200)
        late_night_activity = []
        
        for activity in user_activity:
            if activity.get('last_run'):
                try:
                    dt = datetime.fromisoformat(activity['last_run'].replace('Z', '+00:00'))
                    if dt.hour >= 23 or dt.hour <= 5:  # 11 PM to 5 AM
                        late_night_activity.append(activity)
                except:
                    continue
        
        if late_night_activity:
            suspicious_indicators.append({
                'type': 'late_night_activity',
                'count': len(late_night_activity),
                'description': f'Late-night activity: {len(late_night_activity)} events',
                'items': late_night_activity[:10]
            })
        
        # Check for system tools usage
        system_tools = ['cmd.exe', 'powershell.exe', 'regedit.exe', 'taskmgr.exe', 'netstat.exe']
        tool_usage = []
        
        for activity in user_activity:
            program = activity.get('program_name', '').lower()
            if any(tool in program for tool in system_tools):
                tool_usage.append(activity)
        
        if tool_usage:
            suspicious_indicators.append({
                'type': 'system_tools_usage',
                'count': len(tool_usage),
                'description': f'System tools usage: {len(tool_usage)} instances',
                'items': tool_usage[:10]
            })
        
        # Check for suspicious browsing
        browser_history = self.get_browser_history(case_id, limit=100)
        suspicious_keywords = ['hack', 'crack', 'exploit', 'malware', 'virus', 'trojan']
        suspicious_browsing = []
        
        for entry in browser_history:
            url = entry.get('url', '').lower()
            title = entry.get('title', '').lower()
            if any(keyword in url or keyword in title for keyword in suspicious_keywords):
                suspicious_browsing.append(entry)
        
        if suspicious_browsing:
            suspicious_indicators.append({
                'type': 'suspicious_browsing',
                'count': len(suspicious_browsing),
                'description': f'Potentially suspicious browsing: {len(suspicious_browsing)} entries',
                'items': suspicious_browsing[:10]
            })
        
        return suspicious_indicators
    
    def get_user_behavior_analysis(self, case_id):
        """Analyze user behavior patterns"""
        analysis = {}
        
        # Get most executed programs
        top_programs = self.get_most_executed_programs(case_id, 20)
        analysis['top_programs'] = top_programs
        
        # Analyze activity by hour
        user_activity = self.get_user_activity(case_id, limit=500)
        hour_activity = {}
        
        for activity in user_activity:
            if activity.get('last_run'):
                try:
                    dt = datetime.fromisoformat(activity['last_run'].replace('Z', '+00:00'))
                    hour = dt.hour
                    if hour not in hour_activity:
                        hour_activity[hour] = 0
                    hour_activity[hour] += 1
                except:
                    continue
        
        analysis['activity_by_hour'] = [
            {'hour': hour, 'count': count}
            for hour, count in sorted(hour_activity.items())
        ]
        
        # Analyze program types
        program_types = {}
        for activity in user_activity:
            activity_type = activity.get('activity_type', 'unknown')
            if activity_type not in program_types:
                program_types[activity_type] = 0
            program_types[activity_type] += 1
        
        analysis['program_types'] = [
            {'type': ptype, 'count': count}
            for ptype, count in sorted(program_types.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return analysis
    
    def get_network_analysis(self, case_id):
        """Analyze network-related artifacts"""
        analysis = {}
        
        # Browser history domain analysis
        browser_history = self.get_browser_history(case_id, limit=500)
        domains = {}
        
        for entry in browser_history:
            url = entry.get('url', '')
            if url and '://' in url:
                try:
                    domain = url.split('://')[1].split('/')[0].split('?')[0]
                    if domain not in domains:
                        domains[domain] = {'count': 0, 'visits': 0, 'last_visit': None}
                    domains[domain]['count'] += 1
                    domains[domain]['visits'] += entry.get('visit_count', 1)
                    
                    # Track most recent visit
                    last_visit = entry.get('last_visit')
                    if last_visit and (not domains[domain]['last_visit'] or last_visit > domains[domain]['last_visit']):
                        domains[domain]['last_visit'] = last_visit
                except:
                    continue
        
        # Sort domains by visit count
        top_domains = sorted(domains.items(), key=lambda x: x[1]['visits'], reverse=True)[:20]
        analysis['top_domains'] = [
            {
                'domain': domain,
                'entries': stats['count'],
                'total_visits': stats['visits'],
                'last_visit': stats['last_visit']
            }
            for domain, stats in top_domains
        ]
        
        # Get system network info
        system_info = self.get_system_info(case_id)
        analysis['system_network_info'] = system_info.get('network_info', {})
        
        return analysis
    
    def store_artifacts_from_json(self, json_file_path):
        """Store artifacts from JSON file"""
        return self.storage.store_all_artifacts(json_file_path)


# Global service instance
mongo_service = ForensicMongoService()