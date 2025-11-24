# Manual Django Backend Setup

If the automated setup fails, follow these steps to set up Django manually.

## Prerequisites

### Install System Dependencies (Ubuntu/Debian)

```bash
# PostgreSQL development files
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib libpq-dev

# Python development files
sudo apt-get install -y python3-dev python3-pip

# Optional: Use system psycopg2
sudo apt-get install -y python3-psycopg2
```

## Step-by-Step Setup

### 1. Install Core Requirements

```bash
cd backend

# Install Django and core packages
pip install Django djangorestframework django-cors-headers django-filter

# Install database drivers
pip install pymongo PyYAML requests

# Try psycopg2-binary first
pip install psycopg2-binary

# If that fails, try system psycopg2
pip install psycopg2
```

### 2. Configure Database

Make sure PostgreSQL is running:

```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

Create the database (if not exists):

```bash
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE forensics;
CREATE USER dhanush WITH PASSWORD 'dkarcher';
GRANT ALL PRIVILEGES ON DATABASE forensics TO dhanush;
\q
```

### 3. Run Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# If you get errors, try:
python manage.py migrate --run-syncdb
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 5. Create User Profiles

```bash
python manage.py create_superuser_profile
```

### 6. Import Case

```bash
python manage.py import_case ../test_comprehensive_artifacts.json \
  --title "NPS 2008 Jean Investigation" \
  --description "Forensic analysis of disk image" \
  --user admin \
  --priority high
```

### 7. Start Server

```bash
python manage.py runserver
```

Access at:
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

## Troubleshooting

### psycopg2 Installation Issues

**Error**: `pg_config executable not found`

**Solution**:
```bash
sudo apt-get install libpq-dev
pip install psycopg2
```

**Alternative**: Use system package
```bash
sudo apt-get install python3-psycopg2
```

### Database Connection Issues

**Error**: `could not connect to server`

**Solution**:
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Start if not running
sudo systemctl start postgresql

# Check if database exists
sudo -u postgres psql -l | grep forensics
```

### Migration Issues

**Error**: `No migrations to apply`

**Solution**:
```bash
# Force create migrations
python manage.py makemigrations forensic_api

# Apply with sync
python manage.py migrate --run-syncdb
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'forensic_api'`

**Solution**:
```bash
# Make sure you're in the backend directory
cd backend

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Try again
python manage.py migrate
```

## Alternative: Use SQLite (Development Only)

If PostgreSQL is causing issues, you can use SQLite for testing:

Edit `forensic_backend/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

Then run migrations:
```bash
python manage.py migrate
python manage.py createsuperuser
```

## Minimal Installation

If you just want to test the API without all features:

```bash
# Install only essentials
pip install Django djangorestframework pymongo

# Use SQLite (edit settings.py as shown above)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver
```

## Verify Installation

Test that everything works:

```bash
# Test Django
python manage.py check

# Test database connection
python manage.py dbshell

# List migrations
python manage.py showmigrations

# Test import
python manage.py shell
>>> from forensic_api.models import ForensicCase
>>> ForensicCase.objects.count()
```

## Success Checklist

- [ ] PostgreSQL/SQLite running
- [ ] MongoDB running
- [ ] Django installed
- [ ] Migrations applied
- [ ] Superuser created
- [ ] Case imported
- [ ] Server starts without errors
- [ ] Can access http://localhost:8000/api/
- [ ] Can login to http://localhost:8000/admin/

## Getting Help

If you're still having issues:

1. Check the error logs in `backend/logs/`
2. Run with debug mode: `export DJANGO_DEBUG=True`
3. Test individual components:
   ```bash
   python manage.py check
   python manage.py test
   ```

## Next Steps

Once Django is running:

1. Access the API at http://localhost:8000/api/
2. Login to admin at http://localhost:8000/admin/
3. View your case at http://localhost:8000/api/cases/
4. Test endpoints with curl or Postman
5. Build a frontend or use the browsable API