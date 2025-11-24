#!/usr/bin/env python3
"""
Show current forensic analysis results
"""

from database.mongodb_retrieval import ForensicMongoRetrieval

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def main():
    print_header("🔬 Forensic Analysis Results")
    
    retrieval = ForensicMongoRetrieval()
    
    try:
        # Get all cases
        cases = retrieval.get_all_cases()
        
        if not cases:
            print("\n❌ No cases found in MongoDB")
            print("Run: python store_artifacts.py test_comprehensive_artifacts.json")
            return
        
        print(f"\n✅ Found {len(cases)} case(s)")
        
        for case in cases:
            case_id = case.get('case_id')
            print(f"\n📁 Case: {case_id}")
            print(f"   Image: {case.get('image_path', 'N/A')}")
            
            # Get summary
            summary = retrieval.get_case_summary(case_id)
            if summary:
                counts = summary.get('counts', {})
                
                print_header("Artifact Counts")
                print(f"  Browser History: {counts.get('browser_history', 0)}")
                print(f"  Browser Cookies: {counts.get('browser_cookies', 0)}")
                print(f"  USB Devices: {counts.get('usb_devices', 0)}")
                print(f"  User Activity: {counts.get('user_activity', 0)}")
                print(f"  Installed Programs: {counts.get('installed_programs', 0)}")
                print(f"  Event Logs: {counts.get('event_logs', 0)}")
                print(f"  Deleted Files: {counts.get('deleted_files', 0)}")
                print(f"  Timeline Events: {counts.get('timeline_events', 0)}")
                
                # Show USB devices
                print_header("USB Devices (Top 5)")
                usb_devices = retrieval.get_usb_devices(case_id)
                for i, device in enumerate(usb_devices[:5], 1):
                    print(f"  {i}. {device.get('friendly_name', 'Unknown')}")
                    print(f"     First Install: {device.get('first_install', 'Unknown')}")
                    print(f"     Device: {device.get('device_name', 'Unknown')}")
                
                if len(usb_devices) > 5:
                    print(f"  ... and {len(usb_devices) - 5} more devices")
                
                # Show top programs
                print_header("Most Executed Programs (Top 10)")
                programs = retrieval.get_most_executed_programs(case_id, 10)
                for i, prog in enumerate(programs, 1):
                    name = prog.get('program_name', 'Unknown')
                    if len(name) > 50:
                        name = name[:47] + "..."
                    print(f"  {i:2d}. {name}")
                    print(f"      Run Count: {prog.get('run_count', 0)}, Last Run: {prog.get('last_run', 'Unknown')}")
                
                # Show installed programs
                print_header("Installed Programs (Top 10)")
                installed = retrieval.get_installed_programs(case_id)
                for i, prog in enumerate(installed[:10], 1):
                    print(f"  {i:2d}. {prog.get('display_name', 'Unknown')}")
                    if prog.get('display_version'):
                        print(f"      Version: {prog['display_version']}")
                    if prog.get('publisher'):
                        print(f"      Publisher: {prog['publisher']}")
                
                if len(installed) > 10:
                    print(f"  ... and {len(installed) - 10} more programs")
                
                # Show recent timeline
                print_header("Recent Timeline Events (Last 10)")
                timeline = retrieval.get_timeline(case_id, limit=10)
                for i, event in enumerate(timeline, 1):
                    print(f"  {i:2d}. {event.get('timestamp', 'Unknown')} - {event.get('event_type', 'Unknown')}")
                    desc = event.get('description', 'No description')
                    if len(desc) > 60:
                        desc = desc[:57] + "..."
                    print(f"      {desc}")
                
                # Show system info
                print_header("System Information")
                system_info = retrieval.get_system_info(case_id)
                
                if system_info.get('last_logged_user'):
                    print("  Last Logged User:")
                    for key, value in system_info['last_logged_user'].items():
                        print(f"    {key}: {value}")
                
                if system_info.get('timezone_info'):
                    print("\n  Timezone:")
                    for key, value in system_info['timezone_info'].items():
                        print(f"    {key}: {value}")
                
                # Show run keys
                print_header("Persistence Mechanisms (Run Keys)")
                run_keys = retrieval.get_run_keys(case_id)
                for i, key in enumerate(run_keys[:5], 1):
                    print(f"  {i}. {key.get('name', 'Unknown')}")
                    value = key.get('value', 'Unknown')
                    if len(value) > 60:
                        value = value[:57] + "..."
                    print(f"     Command: {value}")
                    print(f"     Location: {key.get('key_path', 'Unknown')}")
                
                if len(run_keys) > 5:
                    print(f"  ... and {len(run_keys) - 5} more run keys")
        
        print_header("Analysis Complete")
        print("\n💡 Next Steps:")
        print("  1. Run detailed analysis: python database/query_examples.py")
        print("  2. Search artifacts: python -c \"from database.mongodb_retrieval import ForensicMongoRetrieval; r = ForensicMongoRetrieval(); print(r.search_artifacts('CASE_ID', 'search_term'))\"")
        print("  3. View full report: python analyze_results.py test_comprehensive_artifacts.json")
        print("\n📚 Documentation: See CURRENT_STATUS.md for more details")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure MongoDB is running: sudo systemctl start mongod")
    
    finally:
        retrieval.close()

if __name__ == "__main__":
    main()