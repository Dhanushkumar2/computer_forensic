#!/usr/bin/env python3
"""
Setup script for Django forensic backend
"""
import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        if isinstance(command, list):
            subprocess.run(command, check=True)
        else:
            os.system(command)
        print(f"✅ {description} completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during {description}: {e}")
        return False
    return True

def setup_django():
    """Setup Django application"""
    print("🚀 Setting up Django Forensic Backend")
    print("=" * 50)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forensic_backend.settings')
    
    # Install requirements
    if not run_command([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      "Installing Python requirements"):
        return False
    
    # Setup Django
    django.setup()
    
    # Run migrations
    if not run_command([sys.executable, 'manage.py', 'makemigrations'], 
                      "Creating migrations"):
        return False
    
    if not run_command([sys.executable, 'manage.py', 'migrate'], 
                      "Running migrations"):
        return False
    
    # Create superuser (interactive)
    print("\n📝 Creating superuser account...")
    print("Please provide superuser credentials:")
    try:
        execute_from_command_line(['manage.py', 'createsuperuser'])
        print("✅ Superuser created successfully")
    except KeyboardInterrupt:
        print("\n⚠️  Superuser creation skipped")
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
    
    # Create user profiles
    if not run_command([sys.executable, 'manage.py', 'create_superuser_profile'], 
                      "Creating user profiles"):
        return False
    
    # Collect static files
    if not run_command([sys.executable, 'manage.py', 'collectstatic', '--noinput'], 
                      "Collecting static files"):
        return False
    
    print("\n🎉 Django setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the development server: python manage.py runserver")
    print("2. Import a forensic case: python manage.py import_case path/to/artifacts.json")
    print("3. Access the admin interface: http://localhost:8000/admin/")
    print("4. Access the API: http://localhost:8000/api/")
    
    return True

if __name__ == "__main__":
    if setup_django():
        sys.exit(0)
    else:
        sys.exit(1)