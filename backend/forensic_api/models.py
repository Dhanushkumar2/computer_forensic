"""
Django models for forensic investigation system
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class ForensicCase(models.Model):
    """Main case model stored in PostgreSQL"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('archived', 'Archived'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Primary identifiers
    case_id = models.CharField(max_length=100, unique=True, db_index=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Case metadata
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    case_number = models.CharField(max_length=50, blank=True)
    
    # Image information
    image_path = models.CharField(max_length=500)
    image_name = models.CharField(max_length=200)
    image_size = models.BigIntegerField(null=True, blank=True)
    image_hash_md5 = models.CharField(max_length=32, blank=True)
    image_hash_sha256 = models.CharField(max_length=64, blank=True)
    
    # Processing information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    extraction_time = models.DateTimeField(null=True, blank=True)
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    
    # System information
    ntfs_offset = models.BigIntegerField(null=True, blank=True)
    user_profiles = models.JSONField(default=list, blank=True)
    
    # Assignment and tracking
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_cases')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Statistics (cached from MongoDB)
    total_browser_history = models.IntegerField(default=0)
    total_browser_cookies = models.IntegerField(default=0)
    total_usb_devices = models.IntegerField(default=0)
    total_user_activity = models.IntegerField(default=0)
    total_installed_programs = models.IntegerField(default=0)
    total_deleted_files = models.IntegerField(default=0)
    total_event_logs = models.IntegerField(default=0)
    total_timeline_events = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"{self.case_id} - {self.title}"
    
    def update_statistics(self, stats_dict):
        """Update cached statistics from MongoDB"""
        for key, value in stats_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save(update_fields=list(stats_dict.keys()))


class CaseNote(models.Model):
    """Case notes and comments"""
    
    case = models.ForeignKey(ForensicCase, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Note for {self.case.case_id} by {self.author.username}"


class CaseFile(models.Model):
    """Files associated with cases"""
    
    FILE_TYPE_CHOICES = [
        ('image', 'Disk Image'),
        ('report', 'Report'),
        ('evidence', 'Evidence File'),
        ('export', 'Data Export'),
        ('other', 'Other'),
    ]
    
    case = models.ForeignKey(ForensicCase, on_delete=models.CASCADE, related_name='files')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_path = models.FileField(upload_to='case_files/%Y/%m/%d/')
    file_size = models.BigIntegerField(null=True, blank=True)
    file_hash = models.CharField(max_length=64, blank=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.name} ({self.case.case_id})"


class ExtractionJob(models.Model):
    """Track extraction jobs"""
    
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    case = models.ForeignKey(ForensicCase, on_delete=models.CASCADE, related_name='extraction_jobs')
    job_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    
    # Job details
    extraction_type = models.CharField(max_length=50, default='comprehensive')
    parameters = models.JSONField(default=dict, blank=True)
    
    # Progress tracking
    progress_percentage = models.IntegerField(default=0)
    current_step = models.CharField(max_length=100, blank=True)
    log_messages = models.JSONField(default=list, blank=True)
    
    # Results
    artifacts_extracted = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    output_file_path = models.CharField(max_length=500, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Extraction {self.job_id} for {self.case.case_id}"
    
    def add_log_message(self, message, level='info'):
        """Add a log message to the job"""
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'level': level,
            'message': message
        }
        self.log_messages.append(log_entry)
        self.save(update_fields=['log_messages'])


class SearchQuery(models.Model):
    """Track search queries for analytics"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    case = models.ForeignKey(ForensicCase, on_delete=models.CASCADE, null=True, blank=True)
    query_text = models.CharField(max_length=500)
    query_type = models.CharField(max_length=50)  # 'global', 'browser', 'timeline', etc.
    filters = models.JSONField(default=dict, blank=True)
    results_count = models.IntegerField(default=0)
    execution_time = models.FloatField(null=True, blank=True)  # in seconds
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Search: {self.query_text[:50]}..."


class UserProfile(models.Model):
    """Extended user profile for forensic investigators"""
    
    ROLE_CHOICES = [
        ('investigator', 'Investigator'),
        ('analyst', 'Analyst'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='investigator')
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Preferences
    default_case_view = models.CharField(max_length=50, default='list')
    items_per_page = models.IntegerField(default=25)
    email_notifications = models.BooleanField(default=True)
    
    # Statistics
    cases_created = models.IntegerField(default=0)
    cases_completed = models.IntegerField(default=0)
    total_searches = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.role})"


class AuditLog(models.Model):
    """Audit trail for all system actions"""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('search', 'Search'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)  # 'case', 'artifact', etc.
    resource_id = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.resource_type} at {self.timestamp}"