"""
Django REST Framework serializers for forensic API
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    ForensicCase, CaseNote, CaseFile, ExtractionJob, 
    SearchQuery, UserProfile, AuditLog
)


class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'user', 'role', 'department', 'phone', 'default_case_view',
            'items_per_page', 'email_notifications', 'cases_created',
            'cases_completed', 'total_searches', 'created_at', 'updated_at'
        ]
        read_only_fields = ['cases_created', 'cases_completed', 'total_searches', 'created_at', 'updated_at']


class ForensicCaseSerializer(serializers.ModelSerializer):
    """Forensic case serializer"""
    
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = ForensicCase
        fields = [
            'id', 'case_id', 'uuid', 'title', 'description', 'case_number',
            'image_path', 'image_name', 'image_size', 'image_hash_md5', 'image_hash_sha256',
            'status', 'priority', 'extraction_time', 'processing_started', 'processing_completed',
            'ntfs_offset', 'user_profiles', 'assigned_to', 'assigned_to_id', 'created_by',
            'created_at', 'updated_at', 'total_browser_history', 'total_browser_cookies',
            'total_usb_devices', 'total_user_activity', 'total_installed_programs',
            'total_deleted_files', 'total_event_logs', 'total_timeline_events'
        ]
        read_only_fields = [
            'id', 'uuid', 'created_by', 'created_at', 'updated_at',
            'total_browser_history', 'total_browser_cookies', 'total_usb_devices',
            'total_user_activity', 'total_installed_programs', 'total_deleted_files',
            'total_event_logs', 'total_timeline_events'
        ]
    
    def create(self, validated_data):
        """Create a new forensic case"""
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        if assigned_to_id:
            validated_data['assigned_to_id'] = assigned_to_id
        
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CaseNoteSerializer(serializers.ModelSerializer):
    """Case note serializer"""
    
    author = UserSerializer(read_only=True)
    case_id = serializers.CharField(source='case.case_id', read_only=True)
    
    class Meta:
        model = CaseNote
        fields = [
            'id', 'case', 'case_id', 'author', 'title', 'content',
            'is_important', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create a new case note"""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class CaseFileSerializer(serializers.ModelSerializer):
    """Case file serializer"""
    
    uploaded_by = UserSerializer(read_only=True)
    case_id = serializers.CharField(source='case.case_id', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CaseFile
        fields = [
            'id', 'case', 'case_id', 'file_type', 'name', 'description',
            'file_path', 'file_url', 'file_size', 'file_hash',
            'uploaded_by', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'file_size', 'file_hash']
    
    def get_file_url(self, obj):
        """Get file URL"""
        if obj.file_path:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file_path.url)
        return None
    
    def create(self, validated_data):
        """Create a new case file"""
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class ExtractionJobSerializer(serializers.ModelSerializer):
    """Extraction job serializer"""
    
    case_id = serializers.CharField(source='case.case_id', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ExtractionJob
        fields = [
            'id', 'case', 'case_id', 'job_id', 'status', 'extraction_type',
            'parameters', 'progress_percentage', 'current_step', 'log_messages',
            'artifacts_extracted', 'error_message', 'output_file_path',
            'created_at', 'started_at', 'completed_at', 'duration'
        ]
        read_only_fields = [
            'id', 'job_id', 'log_messages', 'created_at', 'started_at', 'completed_at'
        ]
    
    def get_duration(self, obj):
        """Calculate job duration"""
        if obj.started_at and obj.completed_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None


class SearchQuerySerializer(serializers.ModelSerializer):
    """Search query serializer"""
    
    user = UserSerializer(read_only=True)
    case_id = serializers.CharField(source='case.case_id', read_only=True, allow_null=True)
    
    class Meta:
        model = SearchQuery
        fields = [
            'id', 'user', 'case', 'case_id', 'query_text', 'query_type',
            'filters', 'results_count', 'execution_time', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        """Create a new search query"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'action', 'resource_type', 'resource_id',
            'details', 'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = ['id', 'user', 'timestamp']


# MongoDB artifact serializers (for API responses)
class BrowserArtifactSerializer(serializers.Serializer):
    """Browser artifact serializer"""
    
    case_id = serializers.CharField()
    artifact_type = serializers.CharField()
    browser_type = serializers.CharField()
    url = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField(required=False, allow_blank=True)
    visit_count = serializers.IntegerField(required=False)
    last_visit = serializers.DateTimeField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)
    value = serializers.CharField(required=False, allow_blank=True)
    host = serializers.CharField(required=False, allow_blank=True)
    path = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField()


class USBDeviceSerializer(serializers.Serializer):
    """USB device serializer"""
    
    case_id = serializers.CharField()
    device_class = serializers.CharField()
    device_name = serializers.CharField()
    instance_id = serializers.CharField()
    friendly_name = serializers.CharField(required=False, allow_blank=True)
    first_install = serializers.DateTimeField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()


class UserActivitySerializer(serializers.Serializer):
    """User activity serializer"""
    
    case_id = serializers.CharField()
    program_name = serializers.CharField()
    activity_type = serializers.CharField()
    run_count = serializers.IntegerField()
    last_run = serializers.DateTimeField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField(required=False, allow_null=True)
    created_at = serializers.DateTimeField()


class TimelineEventSerializer(serializers.Serializer):
    """Timeline event serializer"""
    
    case_id = serializers.CharField()
    timestamp = serializers.DateTimeField()
    event_type = serializers.CharField()
    description = serializers.CharField()
    source = serializers.CharField()
    source_id = serializers.CharField()
    created_at = serializers.DateTimeField()


class CaseSummarySerializer(serializers.Serializer):
    """Case summary serializer"""
    
    case_id = serializers.CharField()
    image_path = serializers.CharField()
    extraction_time = serializers.DateTimeField()
    user_profiles = serializers.ListField(child=serializers.CharField())
    counts = serializers.DictField()


class SearchResultsSerializer(serializers.Serializer):
    """Search results serializer"""
    
    query = serializers.CharField()
    total_results = serializers.IntegerField()
    execution_time = serializers.FloatField()
    results = serializers.DictField()


class StatisticsSerializer(serializers.Serializer):
    """Statistics serializer"""
    
    case_id = serializers.CharField()
    browser_stats = serializers.ListField()
    top_domains = serializers.ListField()
    activity_by_hour = serializers.ListField()
    usb_manufacturers = serializers.ListField()