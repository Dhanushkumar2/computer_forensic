"""
Django management command to create user profiles for existing users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from forensic_api.models import UserProfile


class Command(BaseCommand):
    help = 'Create user profiles for existing users'
    
    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(userprofile__isnull=True)
        
        created_count = 0
        for user in users_without_profiles:
            # Determine role based on user status
            if user.is_superuser:
                role = 'admin'
            elif user.is_staff:
                role = 'supervisor'
            else:
                role = 'investigator'
            
            UserProfile.objects.create(
                user=user,
                role=role,
                department='Forensics'
            )
            created_count += 1
            
            self.stdout.write(f'Created profile for user: {user.username} ({role})')
        
        if created_count == 0:
            self.stdout.write('All users already have profiles.')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} user profiles')
            )