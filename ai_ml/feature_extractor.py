"""
Feature Extractor for ML Anomaly Detection
Extracts features from forensic artifacts for GCN/GAT model training
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
import ipaddress
import hashlib

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.mongodb_retrieval import ForensicMongoRetrieval

logger = logging.getLogger(__name__)


class ForensicFeatureExtractor:
    """Extract ML features from forensic artifacts"""
    
    def __init__(self):
        self.retrieval = ForensicMongoRetrieval()
        
        # Activity type mappings
        self.activity_types = {
            'browser_history': 1,
            'browser_cookies': 2,
            'browser_downloads': 3,
            'file_access': 4,
            'program_execution': 5,
            'usb_connection': 6,
            'registry_access': 7,
            'network_connection': 8,
            'login_attempt': 9,
            'file_deletion': 10,
            'system_event': 11,
            'unknown': 0
        }
        
        # Action mappings
        self.actions = {
            'read': 1,
            'write': 2,
            'execute': 3,
            'delete': 4,
            'create': 5,
            'modify': 6,
            'access': 7,
            'download': 8,
            'upload': 9,
            'connect': 10,
            'disconnect': 11,
            'login': 12,
            'logout': 13,
            'unknown': 0
        }
    
    def extract_features_from_case(self, case_id, output_file=None):
        """
        Extract all features for a case and return DataFrame
        
        Args:
            case_id: Case identifier
            output_file: Optional CSV file to save results
            
        Returns:
            pandas.DataFrame: Features ready for ML model
        """
        logger.info(f"Extracting features for case {case_id}")
        
        features = []
        
        # Extract from different artifact types
        features.extend(self._extract_browser_features(case_id))
        features.extend(self._extract_file_features(case_id))
        features.extend(self._extract_program_features(case_id))
        features.extend(self._extract_usb_features(case_id))
        features.extend(self._extract_event_features(case_id))
        features.extend(self._extract_network_features(case_id))
        
        if not features:
            logger.warning(f"No features extracted for case {case_id}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(features)
        
        # Add derived features
        df = self._add_derived_features(df)
        
        # Add anomaly labels (placeholder - would be from actual analysis)
        df = self._add_anomaly_labels(df)
        
        # Ensure all required columns exist
        df = self._ensure_required_columns(df)
        
        logger.info(f"Extracted {len(df)} feature records for case {case_id}")
        
        if output_file:
            df.to_csv(output_file, index=False)
            logger.info(f"Features saved to {output_file}")
        
        return df
    
    def _extract_browser_features(self, case_id):
        """Extract features from browser artifacts"""
        features = []
        
        # Browser history
        history = self.retrieval.get_browser_history(case_id)
        for entry in history or []:
            try:
                timestamp = self._parse_timestamp(entry.get('last_visit'))
                if not timestamp:
                    continue
                
                features.append({
                    'User_ID': self._extract_user_id(entry),
                    'Activity_Type': self.activity_types['browser_history'],
                    'Resource_Accessed': self._hash_resource(entry.get('url', '')),
                    'Action': self.actions['access'],
                    'Login_Attempts': 0,
                    'File_Size': len(entry.get('title', '')) + len(entry.get('url', '')),
                    'Hour': timestamp.hour,
                    'Timestamp': timestamp,
                    'IP_Address': self._extract_ip_from_url(entry.get('url', '')),
                    'File_Info': entry.get('title', ''),
                    'Visit_Count': entry.get('visit_count', 1)
                })
            except Exception as e:
                logger.warning(f"Error processing browser history entry: {e}")
                continue
        
        # Browser downloads
        downloads = self.retrieval.get_browser_downloads(case_id)
        for entry in downloads or []:
            try:
                timestamp = self._parse_timestamp(entry.get('start_time'))
                if not timestamp:
                    continue
                
                features.append({
                    'User_ID': self._extract_user_id(entry),
                    'Activity_Type': self.activity_types['browser_downloads'],
                    'Resource_Accessed': self._hash_resource(entry.get('target_path', '')),
                    'Action': self.actions['download'],
                    'Login_Attempts': 0,
                    'File_Size': entry.get('total_bytes', 0),
                    'Hour': timestamp.hour,
                    'Timestamp': timestamp,
                    'IP_Address': self._extract_ip_from_url(entry.get('url', '')),
                    'File_Info': entry.get('target_path', ''),
                    'Download_State': entry.get('state', 'unknown')
                })
            except Exception as e:
                logger.warning(f"Error processing browser download entry: {e}")
                continue
        
        return features
    
    def _extract_file_features(self, case_id):
        """Extract features from file system artifacts"""
        features = []
        
        # File system artifacts
        files = self.retrieval.get_filesystem_artifacts(case_id)
        for entry in files or []:
            try:
                timestamp = self._parse_timestamp(entry.get('modified_time'))
                if not timestamp:
                    continue
                
                features.append({
                    'User_ID': self._extract_user_id(entry),
                    'Activity_Type': self.activity_types['file_access'],
                    'Resource_Accessed': self._hash_resource(entry.get('file_path', '')),
                    'Action': self._determine_file_action(entry),
                    'Login_Attempts': 0,
                    'File_Size': entry.get('file_size', 0),
                    'Hour': timestamp.hour,
                    'Timestamp': timestamp,
                    'IP_Address': '127.0.0.1',  # Local file access
                    'File_Info': entry.get('file_name', ''),
                    'File_Type': entry.get('file_type', 'unknown')
                })
            except Exception as e:
                logger.warning(f"Error processing file entry: {e}")
                continue
        
        # Deleted files
        deleted = self.retrieval.get_deleted_files(case_id)
        for entry in deleted or []:
            try:
                timestamp = self._parse_timestamp(entry.get('deleted_time'))
                if not timestamp:
                    continue
                
                features.append({
                    'User_ID': self._extract_user_id(entry),
                    'Activity_Type': self.activity_types['file_deletion'],
                    'Resource_Accessed': self._hash_resource(entry.get('original_filename', '')),
                    'Action': self.actions['delete'],
                    'Login_Attempts': 0,
                    'File_Size': entry.get('file_size', 0),
                    'Hour': timestamp.hour,
                    'Timestamp': timestamp,
                    'IP_Address': '127.0.0.1',
                    'File_Info': entry.get('original_filename', ''),
                    'Recovery_Status': entry.get('recovery_status', 'unknown')
                })
            except Exception as e:
                logger.warning(f"Error processing deleted file entry: {e}")
                continue
        
        return features
    
    def _extract_program_features(self, case_id):
        """Extract features from program execution"""
        features = []
        
        # User activity (program execution)
        activity = self.retrieval.get_user_activity(case_id)
        for entry in activity or []:
            try:
                timestamp = self._parse_timestamp(entry.get('last_run'))
                if not timestamp:
                    continue
                
                features.append({
                    'User_ID': self._extract_user_id(entry),
                    'Activity_Type': self.activity_types['program_execution'],
                    'Resource_Accessed': self._hash_resource(entry.get('program_name', '')),
                    'Action': self.actions['execute'],
                    'Login_Attempts': 0,
                    'File_Size': 0,  # Program size not typically available
                    'Hour': timestamp.hour,
                    'Timestamp': timestamp,
                    'IP_Address': '127.0.0.1',
                    'File_Info': entry.get('program_name', ''),
                    'Run_Count': entry.get('run_count', 1)
                })
            except Exception as e:
                logger.warning(f"Error processing program execution entry: {e}")
                continue
        
        return features
    
    def _extract_usb_features(self, case_id):
        """Extract features from USB device connections"""
        features = []
        
        usb_devices = self.retrieval.get_usb_devices(case_id)
        for entry in usb_devices or []:
            try:
                # First connection
                timestamp = self._parse_timestamp(entry.get('first_connection'))
                if timestamp:
                    features.append({
                        'User_ID': self._extract_user_id(entry),
                        'Activity_Type': self.activity_types['usb_connection'],
                        'Resource_Accessed': self._hash_resource(entry.get('device_id', '')),
                        'Action': self.actions['connect'],
                        'Login_Attempts': 0,
                        'File_Size': 0,
                        'Hour': timestamp.hour,
                        'Timestamp': timestamp,
                        'IP_Address': '127.0.0.1',
                        'File_Info': entry.get('device_name', ''),
                        'Device_Serial': entry.get('serial_number', '')
                    })
                
                # Last connection
                timestamp = self._parse_timestamp(entry.get('last_connection'))
                if timestamp:
                    features.append({
                        'User_ID': self._extract_user_id(entry),
                        'Activity_Type': self.activity_types['usb_connection'],
                        'Resource_Accessed': self._hash_resource(entry.get('device_id', '')),
                        'Action': self.actions['disconnect'],
                        'Login_Attempts': 0,
                        'File_Size': 0,
                        'Hour': timestamp.hour,
                        'Timestamp': timestamp,
                        'IP_Address': '127.0.0.1',
                        'File_Info': entry.get('device_name', ''),
                        'Device_Serial': entry.get('serial_number', '')
                    })
            except Exception as e:
                logger.warning(f"Error processing USB entry: {e}")
                continue
        
        return features
    
    def _extract_event_features(self, case_id):
        """Extract features from system events"""
        features = []
        
        # Event logs
        events = self.retrieval.get_event_logs(case_id)
        for entry in events or []:
            try:
                timestamp = self._parse_timestamp(entry.get('time_generated'))
                if not timestamp:
                    continue
                
                # Detect login attempts
                login_attempts = 1 if 'logon' in entry.get('event_type', '').lower() else 0
                
                features.append({
                    'User_ID': self._extract_user_id(entry),
                    'Activity_Type': self.activity_types['system_event'],
                    'Resource_Accessed': self._hash_resource(entry.get('source_name', '')),
                    'Action': self._determine_event_action(entry),
                    'Login_Attempts': login_attempts,
                    'File_Size': 0,
                    'Hour': timestamp.hour,
                    'Timestamp': timestamp,
                    'IP_Address': entry.get('computer_name', '127.0.0.1'),
                    'File_Info': entry.get('message', ''),
                    'Event_ID': entry.get('event_id', 0)
                })
            except Exception as e:
                logger.warning(f"Error processing event entry: {e}")
                continue
        
        return features
    
    def _extract_network_features(self, case_id):
        """Extract features from network-related artifacts"""
        features = []
        
        # Browser history contains network activity
        history = self.retrieval.get_browser_history(case_id)
        for entry in history or []:
            try:
                timestamp = self._parse_timestamp(entry.get('last_visit'))
                if not timestamp:
                    continue
                
                url = entry.get('url', '')
                if url and ('http' in url or 'https' in url):
                    features.append({
                        'User_ID': self._extract_user_id(entry),
                        'Activity_Type': self.activity_types['network_connection'],
                        'Resource_Accessed': self._hash_resource(url),
                        'Action': self.actions['connect'],
                        'Login_Attempts': 0,
                        'File_Size': len(url),
                        'Hour': timestamp.hour,
                        'Timestamp': timestamp,
                        'IP_Address': self._extract_ip_from_url(url),
                        'File_Info': entry.get('title', ''),
                        'Domain': self._extract_domain(url)
                    })
            except Exception as e:
                logger.warning(f"Error processing network entry: {e}")
                continue
        
        return features
    
    def _add_derived_features(self, df):
        """Add derived features required by the ML model"""
        if df.empty:
            return df
        
        # File_Info_Missing
        df['File_Info_Missing'] = df['File_Info'].isna().astype(int)
        
        # Login_Info_Missing (based on login attempts)
        df['Login_Info_Missing'] = (df['Login_Attempts'] == 0).astype(int)
        
        # Action_Missing
        df['Action_Missing'] = (df['Action'] == 0).astype(int)
        
        # Anomaly_Missing (placeholder)
        df['Anomaly_Missing'] = 0
        
        # Day of week features
        df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
        df['IsWeekend'] = (df['DayOfWeek'] >= 5).astype(int)
        
        # IP address features
        df['IP1'] = df['IP_Address'].apply(lambda x: self._get_ip_octet(x, 0))
        df['IP2'] = df['IP_Address'].apply(lambda x: self._get_ip_octet(x, 1))
        df['IP3'] = df['IP_Address'].apply(lambda x: self._get_ip_octet(x, 2))
        df['IP4'] = df['IP_Address'].apply(lambda x: self._get_ip_octet(x, 3))
        df['IsPrivateIP'] = df['IP_Address'].apply(self._is_private_ip).astype(int)
        
        # File size log
        df['File_Size_Log'] = np.log1p(df['File_Size'])
        
        return df
    
    def _add_anomaly_labels(self, df):
        """Add anomaly labels based on heuristics"""
        if df.empty:
            return df
        
        # Initialize all as normal
        df['Anomaly_Label'] = 0
        
        # Heuristic-based anomaly detection
        
        # 1. Late night activity (11 PM - 5 AM)
        late_night = (df['Hour'] >= 23) | (df['Hour'] <= 5)
        df.loc[late_night, 'Anomaly_Label'] = 1
        
        # 2. Large file operations
        large_files = df['File_Size'] > df['File_Size'].quantile(0.95)
        df.loc[large_files, 'Anomaly_Label'] = 1
        
        # 3. Multiple login attempts
        multiple_logins = df['Login_Attempts'] > 3
        df.loc[multiple_logins, 'Anomaly_Label'] = 1
        
        # 4. Weekend activity
        weekend_activity = df['IsWeekend'] == 1
        df.loc[weekend_activity, 'Anomaly_Label'] = 1
        
        # 5. External IP connections
        external_ips = df['IsPrivateIP'] == 0
        df.loc[external_ips, 'Anomaly_Label'] = 1
        
        # 6. File deletions
        deletions = df['Activity_Type'] == self.activity_types['file_deletion']
        df.loc[deletions, 'Anomaly_Label'] = 1
        
        return df
    
    def _ensure_required_columns(self, df):
        """Ensure all required columns exist with proper data types"""
        required_columns = [
            'User_ID', 'Activity_Type', 'Resource_Accessed', 'Action',
            'Login_Attempts', 'File_Size', 'Hour', 'File_Info_Missing',
            'Login_Info_Missing', 'Action_Missing', 'Anomaly_Missing',
            'DayOfWeek', 'IsWeekend', 'IP1', 'IP2', 'IP3', 'IP4',
            'IsPrivateIP', 'File_Size_Log', 'Anomaly_Label'
        ]
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Ensure proper data types
        numeric_columns = [
            'User_ID', 'Activity_Type', 'Resource_Accessed', 'Action',
            'Login_Attempts', 'File_Size', 'Hour', 'File_Info_Missing',
            'Login_Info_Missing', 'Action_Missing', 'Anomaly_Missing',
            'DayOfWeek', 'IsWeekend', 'IP1', 'IP2', 'IP3', 'IP4',
            'IsPrivateIP', 'File_Size_Log', 'Anomaly_Label'
        ]
        
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Select only required columns
        df = df[required_columns]
        
        return df
    
    # Helper methods
    def _parse_timestamp(self, timestamp_str):
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return None
        
        try:
            if isinstance(timestamp_str, str):
                # Try different formats
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S.%f',
                    '%Y-%m-%dT%H:%M:%S.%fZ'
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue
            
            return None
        except Exception:
            return None
    
    def _extract_user_id(self, entry):
        """Extract user ID from entry"""
        # Try different fields that might contain user info
        user_fields = ['user_name', 'user', 'account_name', 'username']
        
        for field in user_fields:
            if field in entry and entry[field]:
                return hash(entry[field]) % 10000  # Hash to numeric ID
        
        return 1  # Default user ID
    
    def _hash_resource(self, resource):
        """Hash resource name to numeric ID"""
        if not resource:
            return 0
        return int(hashlib.md5(resource.encode()).hexdigest()[:8], 16) % 100000
    
    def _extract_ip_from_url(self, url):
        """Extract IP address from URL or return default"""
        if not url:
            return '127.0.0.1'
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if hostname:
                # Try to parse as IP
                try:
                    ipaddress.ip_address(hostname)
                    return hostname
                except ValueError:
                    # It's a domain name, return a default IP
                    return '8.8.8.8'  # External IP for domains
            
            return '127.0.0.1'
        except Exception:
            return '127.0.0.1'
    
    def _extract_domain(self, url):
        """Extract domain from URL"""
        if not url:
            return 'localhost'
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or 'localhost'
        except Exception:
            return 'localhost'
    
    def _determine_file_action(self, entry):
        """Determine file action from entry"""
        if 'created' in str(entry).lower():
            return self.actions['create']
        elif 'modified' in str(entry).lower():
            return self.actions['modify']
        elif 'deleted' in str(entry).lower():
            return self.actions['delete']
        else:
            return self.actions['access']
    
    def _determine_event_action(self, entry):
        """Determine action from event entry"""
        event_type = entry.get('event_type', '').lower()
        message = entry.get('message', '').lower()
        
        if 'logon' in event_type or 'login' in message:
            return self.actions['login']
        elif 'logoff' in event_type or 'logout' in message:
            return self.actions['logout']
        elif 'create' in message:
            return self.actions['create']
        elif 'delete' in message:
            return self.actions['delete']
        elif 'modify' in message:
            return self.actions['modify']
        else:
            return self.actions['access']
    
    def _get_ip_octet(self, ip_str, octet_index):
        """Get specific octet from IP address"""
        try:
            octets = ip_str.split('.')
            if len(octets) >= octet_index + 1:
                return int(octets[octet_index])
            return 0
        except Exception:
            return 0
    
    def _is_private_ip(self, ip_str):
        """Check if IP address is private"""
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_private
        except Exception:
            return True  # Default to private if can't parse
    
    def close(self):
        """Close database connections"""
        self.retrieval.close()


def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract ML features from forensic case')
    parser.add_argument('case_id', help='Case ID to process')
    parser.add_argument('--output', '-o', help='Output CSV file')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Extract features
    extractor = ForensicFeatureExtractor()
    
    try:
        df = extractor.extract_features_from_case(args.case_id, args.output)
        
        if not df.empty:
            print(f"\nExtracted {len(df)} feature records")
            print(f"Columns: {list(df.columns)}")
            print(f"Anomaly distribution:")
            print(df['Anomaly_Label'].value_counts())
            
            if args.output:
                print(f"Features saved to: {args.output}")
        else:
            print("No features extracted")
    
    finally:
        extractor.close()


if __name__ == '__main__':
    main()