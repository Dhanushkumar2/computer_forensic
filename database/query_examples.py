#!/usr/bin/env python3
"""
query_examples.py
Example queries and analysis scripts for forensic data
"""

from mongodb_retrieval import ForensicMongoRetrieval
from datetime import datetime, timedelta
import json


class ForensicAnalyzer:
    def __init__(self):
        self.retrieval = ForensicMongoRetrieval()
    
    def analyze_case(self, case_id):
        """Comprehensive case analysis"""
        print(f"=== FORENSIC ANALYSIS FOR CASE: {case_id} ===\n")
        
        # Get case summary
        summary = self.retrieval.get_case_summary(case_id)
        if not summary:
            print(f"Case {case_id} not found!")
            return
        
        print("CASE OVERVIEW:")
        print(f"Image: {summary['image_path']}")
        print(f"Extraction Time: {summary['extraction_time']}")
        print(f"User Profiles: {len(summary['user_profiles'])}")
        for profile in summary['user_profiles']:
            print(f"  - {profile}")
        
        print(f"\nARTIFACT COUNTS:")
        counts = summary['counts']
        for artifact_type, count in counts.items():
            print(f"  {artifact_type.replace('_', ' ').title()}: {count}")
        
        # Detailed analysis
        self.analyze_usb_activity(case_id)
        self.analyze_user_behavior(case_id)
        self.analyze_browser_activity(case_id)
        self.analyze_persistence_mechanisms(case_id)
        self.analyze_timeline(case_id)
        self.analyze_suspicious_activity(case_id)
    
    def analyze_usb_activity(self, case_id):
        """Analyze USB device activity"""
        print(f"\n=== USB DEVICE ANALYSIS ===")
        
        usb_devices = self.retrieval.get_usb_devices(case_id)
        print(f"Total USB devices connected: {len(usb_devices)}")
        
        if usb_devices:
            print("\nUSB Device Timeline:")
            for i, device in enumerate(usb_devices[:10]):
                print(f"{i+1:2d}. {device.get('first_install', 'Unknown time')}")
                print(f"    Device: {device.get('friendly_name', device.get('device_name'))}")
                print(f"    Class: {device.get('device_class')}")
                print(f"    Instance: {device.get('instance_id')}")
        
        # Check for suspicious USB activity
        suspicious_keywords = ['hack', 'crack', 'tool', 'pen', 'test']
        suspicious_devices = []
        for device in usb_devices:
            device_name = device.get('friendly_name', '').lower()
            if any(keyword in device_name for keyword in suspicious_keywords):
                suspicious_devices.append(device)
        
        if suspicious_devices:
            print(f"\n⚠️  POTENTIALLY SUSPICIOUS USB DEVICES ({len(suspicious_devices)}):")
            for device in suspicious_devices:
                print(f"  - {device.get('friendly_name')}")
                print(f"    Connected: {device.get('first_install')}")
    
    def analyze_user_behavior(self, case_id):
        """Analyze user behavior patterns"""
        print(f"\n=== USER BEHAVIOR ANALYSIS ===")
        
        # Get most executed programs
        top_programs = self.retrieval.get_most_executed_programs(case_id, 15)
        print(f"Most Frequently Executed Programs:")
        
        for i, prog in enumerate(top_programs):
            if prog.get('program_name') and len(prog['program_name']) > 3:
                print(f"{i+1:2d}. {prog['program_name']}")
                print(f"    Run Count: {prog.get('run_count', 0)}")
                print(f"    Last Run: {prog.get('last_run', 'Unknown')}")
                print(f"    Type: {prog.get('activity_type', 'Unknown')}")
        
        # Analyze program execution patterns
        user_activity = self.retrieval.get_user_activity(case_id, limit=200)
        
        # Group by time of day
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
        
        if hour_activity:
            print(f"\nActivity by Hour of Day:")
            for hour in sorted(hour_activity.keys()):
                bar = "█" * (hour_activity[hour] // 2)
                print(f"  {hour:2d}:00 - {hour_activity[hour]:3d} activities {bar}")
    
    def analyze_browser_activity(self, case_id):
        """Analyze web browsing behavior"""
        print(f"\n=== BROWSER ACTIVITY ANALYSIS ===")
        
        # Get browser history
        history = self.retrieval.get_browser_history(case_id, limit=50)
        print(f"Total browser history entries analyzed: {len(history)}")
        
        if history:
            # Analyze domains
            domains = {}
            for entry in history:
                url = entry.get('url', '')
                if url and '://' in url:
                    try:
                        domain = url.split('://')[1].split('/')[0].split('?')[0]
                        if domain not in domains:
                            domains[domain] = {'count': 0, 'visits': 0}
                        domains[domain]['count'] += 1
                        domains[domain]['visits'] += entry.get('visit_count', 1)
                    except:
                        continue
            
            print(f"\nTop Visited Domains:")
            sorted_domains = sorted(domains.items(), key=lambda x: x[1]['visits'], reverse=True)
            for i, (domain, stats) in enumerate(sorted_domains[:10]):
                print(f"{i+1:2d}. {domain}")
                print(f"    Entries: {stats['count']}, Total Visits: {stats['visits']}")
        
        # Check for suspicious browsing
        suspicious_keywords = ['hack', 'crack', 'exploit', 'malware', 'virus', 'trojan']
        suspicious_history = []
        for entry in history:
            url = entry.get('url', '').lower()
            title = entry.get('title', '').lower()
            if any(keyword in url or keyword in title for keyword in suspicious_keywords):
                suspicious_history.append(entry)
        
        if suspicious_history:
            print(f"\n⚠️  POTENTIALLY SUSPICIOUS BROWSING ({len(suspicious_history)} entries):")
            for entry in suspicious_history[:5]:
                print(f"  - {entry.get('url', 'Unknown URL')}")
                print(f"    Title: {entry.get('title', 'No title')}")
                print(f"    Last Visit: {entry.get('last_visit', 'Unknown')}")
    
    def analyze_persistence_mechanisms(self, case_id):
        """Analyze persistence mechanisms"""
        print(f"\n=== PERSISTENCE ANALYSIS ===")
        
        run_keys = self.retrieval.get_run_keys(case_id)
        print(f"Total persistence entries found: {len(run_keys)}")
        
        if run_keys:
            print(f"\nPersistence Mechanisms:")
            for i, key in enumerate(run_keys):
                print(f"{i+1:2d}. {key.get('name', 'Unknown')}")
                print(f"    Command: {key.get('value', 'Unknown')}")
                print(f"    Location: {key.get('key_path', 'Unknown')}")
                print(f"    Type: {key.get('type', 'Unknown')}")
        
        # Check for suspicious persistence
        suspicious_persistence = []
        suspicious_paths = ['temp', 'appdata', 'programdata', '%temp%']
        
        for key in run_keys:
            value = key.get('value', '').lower()
            if any(path in value for path in suspicious_paths):
                suspicious_persistence.append(key)
        
        if suspicious_persistence:
            print(f"\n⚠️  POTENTIALLY SUSPICIOUS PERSISTENCE ({len(suspicious_persistence)}):")
            for key in suspicious_persistence:
                print(f"  - {key.get('name')}: {key.get('value')}")
    
    def analyze_timeline(self, case_id, days_back=7):
        """Analyze recent timeline activity"""
        print(f"\n=== TIMELINE ANALYSIS (Last {days_back} days) ===")
        
        end_date = datetime.now().isoformat()
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        
        timeline = self.retrieval.get_timeline(case_id, start_date, end_date, limit=50)
        print(f"Timeline events in last {days_back} days: {len(timeline)}")
        
        if timeline:
            # Group by event type
            event_types = {}
            for event in timeline:
                event_type = event.get('event_type', 'Unknown')
                if event_type not in event_types:
                    event_types[event_type] = 0
                event_types[event_type] += 1
            
            print(f"\nEvent Types:")
            for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {event_type}: {count}")
            
            print(f"\nRecent Timeline Events:")
            for i, event in enumerate(timeline[:10]):
                print(f"{i+1:2d}. {event.get('timestamp', 'Unknown time')} - {event.get('event_type', 'Unknown')}")
                print(f"    {event.get('description', 'No description')}")
    
    def analyze_suspicious_activity(self, case_id):
        """Look for potentially suspicious activity"""
        print(f"\n=== SUSPICIOUS ACTIVITY ANALYSIS ===")
        
        suspicious_indicators = []
        
        # Check for deleted files
        deleted_files = self.retrieval.get_deleted_files(case_id)
        if deleted_files:
            # Look for suspicious file types
            suspicious_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
            suspicious_deletions = []
            
            for file_entry in deleted_files:
                filename = file_entry.get('original_filename', '').lower()
                if any(filename.endswith(ext) for ext in suspicious_extensions):
                    suspicious_deletions.append(file_entry)
            
            if suspicious_deletions:
                suspicious_indicators.append(f"Deleted executable files: {len(suspicious_deletions)}")
        
        # Check for late-night activity
        user_activity = self.retrieval.get_user_activity(case_id, limit=100)
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
            suspicious_indicators.append(f"Late-night activity: {len(late_night_activity)} events")
        
        # Check for system tools usage
        system_tools = ['cmd.exe', 'powershell.exe', 'regedit.exe', 'taskmgr.exe', 'netstat.exe']
        tool_usage = []
        
        for activity in user_activity:
            program = activity.get('program_name', '').lower()
            if any(tool in program for tool in system_tools):
                tool_usage.append(activity)
        
        if tool_usage:
            suspicious_indicators.append(f"System tools usage: {len(tool_usage)} instances")
        
        # Report findings
        if suspicious_indicators:
            print("⚠️  SUSPICIOUS INDICATORS FOUND:")
            for indicator in suspicious_indicators:
                print(f"  - {indicator}")
        else:
            print("✅ No obvious suspicious indicators found")
    
    def search_case(self, case_id, search_term):
        """Search across all artifacts for a term"""
        print(f"\n=== SEARCH RESULTS FOR: '{search_term}' ===")
        
        results = self.retrieval.search_artifacts(case_id, search_term)
        
        total_results = sum(len(artifacts) for artifacts in results.values())
        print(f"Total results found: {total_results}")
        
        for collection, artifacts in results.items():
            if artifacts:
                print(f"\n{collection.replace('_', ' ').title()} ({len(artifacts)} results):")
                for i, artifact in enumerate(artifacts[:5]):  # Show first 5
                    if collection == 'browser_artifacts':
                        print(f"  {i+1}. {artifact.get('url', 'No URL')} - {artifact.get('title', 'No title')}")
                    elif collection == 'user_activity':
                        print(f"  {i+1}. {artifact.get('program_name', 'Unknown program')}")
                    elif collection == 'installed_programs':
                        print(f"  {i+1}. {artifact.get('display_name', 'Unknown program')}")
                    elif collection == 'filesystem_artifacts':
                        print(f"  {i+1}. {artifact.get('filename', 'Unknown file')}")
                    elif collection == 'recycle_bin_artifacts':
                        print(f"  {i+1}. {artifact.get('original_filename', 'Unknown file')}")
                
                if len(artifacts) > 5:
                    print(f"  ... and {len(artifacts) - 5} more results")
    
    def generate_report(self, case_id, output_file=None):
        """Generate comprehensive forensic report"""
        if output_file is None:
            output_file = f"forensic_report_{case_id}.txt"
        
        # Redirect print to file
        import sys
        original_stdout = sys.stdout
        
        with open(output_file, 'w') as f:
            sys.stdout = f
            self.analyze_case(case_id)
        
        sys.stdout = original_stdout
        print(f"Report generated: {output_file}")
    
    def close(self):
        """Close database connection"""
        self.retrieval.close()


def main():
    """Main function with example usage"""
    analyzer = ForensicAnalyzer()
    
    try:
        # List available cases
        cases = analyzer.retrieval.get_all_cases()
        print("Available cases:")
        for case in cases:
            print(f"  - {case['case_id']}: {case.get('image_path', 'Unknown path')}")
        
        if not cases:
            print("No cases found in database. Please run the storage script first.")
            return
        
        # Analyze the first case
        case_id = cases[0]['case_id']
        analyzer.analyze_case(case_id)
        
        # Example searches
        print(f"\n" + "="*60)
        analyzer.search_case(case_id, "flash")
        analyzer.search_case(case_id, "exe")
        
        # Generate report
        analyzer.generate_report(case_id)
        
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()