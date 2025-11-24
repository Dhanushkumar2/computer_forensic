"""
Django admin configuration for forensic API
"""
from django.contrib import admin
from .models import (
    ForensicCase, CaseNote, CaseFile, ExtractionJob,
    SearchQuery, UserProfile, AuditLog
)


@admin.register(ForensicCase)
class ForensicCaseAdmin(admin.ModelAdmin):
    """Admin interface for forensic cases"""
    
    list_display = [
        'case_id', 'title', 'status', 'priority', 'assigned_to',
        'created_by', 'created_at', 'updated_at'
    ]
    list_filter = ['status', 'priority', 'created_at', 'assigned_to']
    search_fields = ['case_id', 'title', 'description', 'case_number']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('case_id', 'uuid', 'title', 'description', 'case_number')
        }),
        ('Image Information', {
            'fields': ('image_path', 'image_name', 'image_size', 'image_hash_md5', 'image_hash_sha256')
        }),
        ('Processing', {
            'fields': ('status', 'priority', 'extraction_time', 'processing_started', 'processing_completed')
        }),
        ('System Information', {
            'fields': ('ntfs_offset', 'user_profiles')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Statistics', {
            'fields': (
                'total_browser_history', 'total_browser_cookies', 'total_usb_devices',
                'total_user_activity', 'total_installed_programs', 'total_deleted_files',
                'total_event_logs', 'total_timeline_events'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    """Admin interface for case notes"""
    
    list_display = ['case', 'title', 'author', 'is_important', 'created_at']
    list_filter = ['is_important', 'created_at', 'author']
    search_fields = ['title', 'content', 'case__case_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CaseFile)
class CaseFileAdmin(admin.ModelAdmin):
    """Admin interface for case files"""
    
    list_display = ['case', 'name', 'file_type', 'file_size', 'uploaded_by', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at', 'uploaded_by']
    search_fields = ['name', 'description', 'case__case_id']
    readonly_fields = ['uploaded_at', 'file_size', 'file_hash']


@admin.register(ExtractionJob)
class ExtractionJobAdmin(admin.ModelAdmin):
    """Admin interface for extraction jobs"""
    
    list_display = ['case', 'job_id', 'status', 'extraction_type', 'progress_percentage', 'created_at']
    list_filter = ['status', 'extraction_type', 'created_at']
    search_fields = ['case__case_id', 'job_id']
    readonly_fields = ['job_id', 'created_at', 'started_at', 'completed_at']


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    """Admin interface for search queries"""
    
    list_display = ['user', 'query_text', 'query_type', 'results_count', 'execution_time', 'created_at']
    list_filter = ['query_type', 'created_at', 'user']
    search_fields = ['query_text', 'user__username']
    readonly_fields = ['created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for user profiles"""
    
    list_display = ['user', 'role', 'department', 'cases_created', 'cases_completed', 'total_searches']
    list_filter = ['role', 'department', 'email_notifications']
    search_fields = ['user__username', 'user__email', 'department']
    readonly_fields = ['cases_created', 'cases_completed', 'total_searches', 'created_at', 'updated_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for audit logs"""
    
    list_display = ['user', 'action', 'resource_type', 'resource_id', 'ip_address', 'timestamp']
    list_filter = ['action', 'resource_type', 'timestamp']
    search_fields = ['user__username', 'resource_type', 'resource_id']
    readonly_fields = ['timestamp']
    
    def has_add_permission(self, request):
        """Disable adding audit logs through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing audit logs through admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting audit logs through admin"""
        return False