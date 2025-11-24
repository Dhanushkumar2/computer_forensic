"""
Django management command to import forensic case from JSON
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from forensic_api.models import ForensicCase
from forensic_api.mongodb_service import mongo_service
import json
import os


class Command(BaseCommand):
    help = 'Import forensic case from JSON file'
    
    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')
        parser.add_argument('--title', type=str, help='Case title')
        parser.add_argument('--description', type=str, help='Case description')
        parser.add_argument('--user', type=str, help='Username of case creator')
        parser.add_argument('--priority', type=str, choices=['low', 'medium', 'high', 'critical'], 
                          default='medium', help='Case priority')
    
    def handle(self, *args, **options):
        json_file = options['json_file']
        
        if not os.path.exists(json_file):
            raise CommandError(f'JSON file "{json_file}" does not exist.')
        
        # Get user
        username = options.get('user', 'admin')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist.')
        
        try:
            # Load JSON data to get case info
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            extraction_info = data.get('extraction_info', {})
            summary = data.get('summary', {})
            
            # Store in MongoDB first
            self.stdout.write('Storing artifacts in MongoDB...')
            case_id = mongo_service.store_artifacts_from_json(json_file)
            
            # Create Django case record
            case = ForensicCase.objects.create(
                case_id=case_id,
                title=options.get('title', f'Case {case_id}'),
                description=options.get('description', f'Imported from {json_file}'),
                image_path=extraction_info.get('image_path', ''),
                image_name=os.path.basename(extraction_info.get('image_path', '')),
                status='completed',
                priority=options['priority'],
                extraction_time=extraction_info.get('extraction_time'),
                ntfs_offset=extraction_info.get('ntfs_offset'),
                user_profiles=extraction_info.get('user_profiles', []),
                created_by=user,
                assigned_to=user,
                # Update statistics from summary
                total_browser_history=summary.get('total_browser_history', 0),
                total_browser_cookies=summary.get('total_browser_cookies', 0),
                total_usb_devices=summary.get('total_usb_devices', 0),
                total_user_activity=summary.get('total_userassist_entries', 0),
                total_installed_programs=summary.get('total_installed_programs', 0),
                total_deleted_files=summary.get('total_deleted_files', 0),
                total_event_logs=summary.get('total_event_log_entries', 0),
                total_timeline_events=summary.get('total_timeline_events', 0),
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported case "{case.case_id}"')
            )
            self.stdout.write(f'Case ID: {case.case_id}')
            self.stdout.write(f'Title: {case.title}')
            self.stdout.write(f'Image: {case.image_path}')
            self.stdout.write(f'Artifacts: {case.total_browser_history + case.total_usb_devices + case.total_user_activity} total')
            
        except Exception as e:
            raise CommandError(f'Error importing case: {e}')