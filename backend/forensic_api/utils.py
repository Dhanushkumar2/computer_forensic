"""
Utility functions for forensic API
"""
from .models import AuditLog


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit_action(user, action, resource_type, resource_id, details=None, request=None):
    """Log an audit action"""
    audit_data = {
        'user': user,
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'details': details or {}
    }
    
    if request:
        audit_data['ip_address'] = get_client_ip(request)
        audit_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
    
    AuditLog.objects.create(**audit_data)