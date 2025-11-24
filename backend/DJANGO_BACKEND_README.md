# Django Forensic Investigation Backend

A comprehensive Django REST API backend for forensic investigation and incident response, integrating with MongoDB for artifact storage and PostgreSQL for case management.

## Features

### 🔍 **Case Management**
- Complete forensic case lifecycle management
- Case assignment and tracking
- Status monitoring and progress tracking
- Multi-user collaboration with role-based access

### 📊 **Artifact Analysis**
- Browser history, cookies, and downloads analysis
- USB device connection tracking
- User activity monitoring (UserAssist data)
- Timeline reconstruction across all artifacts
- Suspicious activity detection

### 🔎 **Advanced Search & Analytics**
- Cross-artifact search capabilities
- Behavioral analysis and pattern detection
- Network activity analysis
- Statistical reporting and visualization data

### 🛡️ **Security & Auditing**
- Complete audit trail for all actions
- Role-based access control
- Secure file handling and storage
- User authentication and authorization

### 🚀 **REST API**
- Comprehensive RESTful API
- Pagination and filtering
- Real-time search capabilities
- Export and reporting endpoints

## Architecture

### Database Design
- **PostgreSQL**: Case metadata, user management, audit logs
- **MongoDB**: Forensic artifacts, timeline events, search data
- **File Storage**: Evidence files, reports, exports

### API Structure
```
/api/
├── cases/              # Forensic cases
├── notes/              # Case notes and comments
├── files/              # Case files and evidence
├── jobs/               # Extraction jobs
├── profiles/           # User profiles
├── searches/           # Search history
└── audit/              # Audit logs
```

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- MongoDB 4.4+
- Redis (for caching and background tasks)

### Quick Setup
```bash
cd backend
python setup_django.py
```

### Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure database (update settings.py)
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create user profiles
python manage.py create_superuser_profile

# Collect static files
python manage.py collectstatic

# Start development server
python manage.py runserver
```

## Configuration

### Database Configuration
Update `forensic_backend/settings.py` or use the YAML config file:

```yaml
# config/db_config.yaml
postgres:
  host: "localhost"
  port: 5432
  user: "your_user"
  password: "your_password"
  database: "forensics"

mongodb:
  uri: "mongodb://localhost:27017/"
  database: "forensics"
```

### Environment Variables
```bash
# Optional: Use environment variables
export DJANGO_SECRET_KEY="your-secret-key"
export DJANGO_DEBUG=True
export DATABASE_URL="postgresql://user:pass@localhost/forensics"
export MONGODB_URI="mongodb://localhost:27017/forensics"
```

## API Usage

### Authentication
```bash
# Get authentication token
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Use token in requests
curl -H "Authorization: Token your-token-here" \
  http://localhost:8000/api/cases/
```

### Case Management

#### Create a Case
```bash
curl -X POST http://localhost:8000/api/cases/ \
  -H "Authorization: Token your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Investigation Case 001",
    "description": "Malware investigation",
    "image_path": "/path/to/image.E01",
    "priority": "high"
  }'
```

#### Get Cases
```bash
# List all cases
curl -H "Authorization: Token your-token" \
  http://localhost:8000/api/cases/

# Filter by status
curl -H "Authorization: Token your-token" \
  "http://localhost:8000/api/cases/?status=completed"

# Search cases
curl -H "Authorization: Token your-token" \
  "http://localhost:8000/api/cases/?search=malware"
```

#### Get Case Summary
```bash
curl -H "Authorization: Token your-token" \
  http://localhost:8000/api/cases/1/summary/
```

### Artifact Analysis

#### Browser History
```bash
# Get all browser history
curl -H "Authorization: Token your-token" \
  http://localhost:8000/api/cases/1/browser_history/

# Filter by browser type
curl -H "Authorization: Token your-token" \
  "http://localhost:8000/api/cases/1/browser_history/?browser_type=firefox"
```

#### USB Devices
```bash
curl -H "Authorization: Token your-token" \
  http://localhost:8000/api/cases/1/usb_devices/
```

#### User Activity
```bash
# Get user activity
curl -H "Authorization: Token your-token" \
  http://localhost:8000/api/cases/1/user_activity/

# Filter by activity type
curl -H "Authorization: Token your-token" \
  "http://localhost:8000/api/cases/1/user_activity/?activity_type=program_execution"
```

#### Timeline Analysis
```bash
# Get timeline
curl -H "Authorization: Token your-token" \
  http://localhost:8000/api/cases/1/timeline/

# Filter by date range
curl -H "Authorization: Token your-token" \
  "http://localhost:8000/api/cases/1/timeline/?start_date=2024-01-01&end_date=2024-01-31"

# Filter by event type
curl -H "Authorization: Token your-token" \
  "http://localhost:8000/api/cases/1/timeline/?event_type=Program Execution"
```

### Search and Analysis

#### Search Artifacts
```bash
# Search across all artifacts
curl -H "Authorization: Token your-token" \
  "http://localhost:8000/api/cases/1/search/?q=malware"

# Search specific collections
curl -H "Authorization: Token your-token" \
  "http://localhost:8000/api/cases/1/search/?q=flash&collections=browser_artifacts&collections=user_activity"
```

#### Suspicious Activity Detection
```bash
curl -H "Authorization: Token your-token" \
  http://localhost:8000/api/cases/1/suspicious_activity/
```

#### Behavior Analysis
```bash
curl -H "Authorization: Token your-token" \
  http://localhost:8000/api/cases/1/behavior_analysis/
```

#### Network Analysis
```bash
curl -H "Authorization: Token your-token" \
  http://localhost:8000/api/cases/1/network_analysis/
```

### Case Notes and Files

#### Add Case Note
```bash
curl -X POST http://localhost:8000/api/notes/ \
  -H "Authorization: Token your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "case": 1,
    "title": "Initial Analysis",
    "content": "Found suspicious activity in browser history",
    "is_important": true
  }'
```

#### Upload Case File
```bash
curl -X POST http://localhost:8000/api/files/ \
  -H "Authorization: Token your-token" \
  -F "case=1" \
  -F "file_type=report" \
  -F "name=Analysis Report" \
  -F "file_path=@report.pdf"
```

## Data Import

### Import Forensic Case
```bash
# Import case from JSON artifacts
python manage.py import_case /path/to/artifacts.json \
  --title "Case 001" \
  --description "Malware investigation" \
  --user admin \
  --priority high
```

### Example Import
```bash
# Import the test case we created earlier
python manage.py import_case ../../test_comprehensive_artifacts.json \
  --title "NPS 2008 Jean Investigation" \
  --description "Analysis of NPS 2008 Jean disk image" \
  --user admin
```

## API Endpoints Reference

### Cases (`/api/cases/`)
- `GET /api/cases/` - List cases
- `POST /api/cases/` - Create case
- `GET /api/cases/{id}/` - Get case details
- `PUT /api/cases/{id}/` - Update case
- `DELETE /api/cases/{id}/` - Delete case
- `GET /api/cases/{id}/summary/` - Get case summary
- `GET /api/cases/{id}/statistics/` - Get case statistics
- `GET /api/cases/{id}/browser_history/` - Get browser history
- `GET /api/cases/{id}/browser_cookies/` - Get browser cookies
- `GET /api/cases/{id}/usb_devices/` - Get USB devices
- `GET /api/cases/{id}/user_activity/` - Get user activity
- `GET /api/cases/{id}/timeline/` - Get timeline
- `GET /api/cases/{id}/search/` - Search artifacts
- `GET /api/cases/{id}/suspicious_activity/` - Get suspicious activity
- `GET /api/cases/{id}/behavior_analysis/` - Get behavior analysis
- `GET /api/cases/{id}/network_analysis/` - Get network analysis

### Notes (`/api/notes/`)
- `GET /api/notes/` - List notes
- `POST /api/notes/` - Create note
- `GET /api/notes/{id}/` - Get note
- `PUT /api/notes/{id}/` - Update note
- `DELETE /api/notes/{id}/` - Delete note

### Files (`/api/files/`)
- `GET /api/files/` - List files
- `POST /api/files/` - Upload file
- `GET /api/files/{id}/` - Get file
- `DELETE /api/files/{id}/` - Delete file

### User Profiles (`/api/profiles/`)
- `GET /api/profiles/` - List profiles
- `GET /api/profiles/me/` - Get current user profile
- `PUT /api/profiles/{id}/` - Update profile

### Audit Logs (`/api/audit/`)
- `GET /api/audit/` - List audit logs (read-only)

## Query Parameters

### Pagination
- `page` - Page number
- `page_size` - Items per page (max 100)

### Filtering
- `status` - Filter by case status
- `priority` - Filter by case priority
- `assigned_to` - Filter by assigned user
- `search` - Search in title, description, case_id

### Date Filtering
- `start_date` - Start date (ISO format)
- `end_date` - End date (ISO format)

### Artifact Filtering
- `browser_type` - Filter by browser type
- `activity_type` - Filter by activity type
- `event_type` - Filter by event type

## Response Format

### Standard Response
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/cases/?page=2",
  "previous": null,
  "results": [...]
}
```

### Error Response
```json
{
  "error": "Error message",
  "details": {...}
}
```

## Security Features

### Authentication
- Token-based authentication
- Session authentication for admin interface
- User permissions and roles

### Authorization
- Role-based access control (Investigator, Analyst, Supervisor, Admin)
- Case-based permissions
- Resource-level access control

### Audit Trail
- Complete audit log for all actions
- IP address and user agent tracking
- Detailed action logging with context

### Data Protection
- Secure file upload handling
- Input validation and sanitization
- SQL injection protection
- XSS protection

## Performance Optimization

### Database Optimization
- Proper indexing on frequently queried fields
- Query optimization with select_related and prefetch_related
- Connection pooling

### Caching
- Redis caching for frequently accessed data
- Query result caching
- Static file caching

### Pagination
- Efficient pagination for large datasets
- Configurable page sizes
- Offset-based pagination

## Monitoring and Logging

### Logging Configuration
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/forensic_backend.log',
        },
    },
    'loggers': {
        'forensic_api': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    },
}
```

### Health Checks
- Database connectivity checks
- MongoDB connection monitoring
- API endpoint health monitoring

## Development

### Running Tests
```bash
python manage.py test
```

### Code Quality
```bash
# Install development dependencies
pip install flake8 black isort

# Format code
black .
isort .

# Check code quality
flake8 .
```

### API Documentation
- Browsable API at `/api/`
- Admin interface at `/admin/`
- API schema available

## Deployment

### Production Settings
```python
# settings/production.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com']
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "forensic_backend.wsgi:application"]
```

### Environment Variables
```bash
export DJANGO_SETTINGS_MODULE=forensic_backend.settings.production
export DATABASE_URL=postgresql://...
export MONGODB_URI=mongodb://...
export REDIS_URL=redis://...
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check PostgreSQL and MongoDB services
   - Verify connection credentials
   - Check firewall settings

2. **Import Errors**
   - Ensure JSON file exists and is valid
   - Check MongoDB connection
   - Verify user permissions

3. **Authentication Issues**
   - Check token validity
   - Verify user permissions
   - Check CORS settings for frontend

4. **Performance Issues**
   - Monitor database queries
   - Check index usage
   - Optimize pagination

### Debug Mode
```bash
export DJANGO_DEBUG=True
python manage.py runserver --settings=forensic_backend.settings
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

This project is licensed under the MIT License.