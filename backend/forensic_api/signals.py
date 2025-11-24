"""
Django signals for forensic API
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, ForensicCase


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=ForensicCase)
def update_user_case_stats(sender, instance, created, **kwargs):
    """Update user statistics when case is created or completed"""
    if created and instance.created_by:
        try:
            profile = instance.created_by.userprofile
            profile.cases_created += 1
            profile.save()
        except UserProfile.DoesNotExist:
            pass
    
    # Update completion stats when case is completed
    if instance.status == 'completed' and instance.assigned_to:
        try:
            profile = instance.assigned_to.userprofile
            profile.cases_completed += 1
            profile.save()
        except UserProfile.DoesNotExist:
            pass