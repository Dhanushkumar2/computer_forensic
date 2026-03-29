"""
Django settings for forensic_backend project.
"""

import os
from pathlib import Path
import yaml

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-forensic-ir-app-development-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'forensic_api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'forensic_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'forensic_backend.wsgi.application'

# Database - Using PostgreSQL for Django models, MongoDB for forensic data
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'forensics',
        'USER': 'dhanush',
        'PASSWORD': 'dkarcher',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Load database configuration
try:
    # Resolve config from project root (forensic_ir_app/config)
    config_path = BASE_DIR.parent / 'config' / 'db_config.yaml'
    with open(config_path, 'r') as f:
        db_config = yaml.safe_load(f)
    
    # MongoDB configuration
    MONGODB_CONFIG = db_config['mongodb']
    
    # Update PostgreSQL config if available
    pg_config = None
    if 'postgres' in db_config:
        pg_config = db_config['postgres']
    elif 'postgresql' in db_config:
        pg_config = db_config['postgresql']

    if pg_config:
        DATABASES['default'].update({
            'NAME': pg_config.get('database', DATABASES['default']['NAME']),
            'USER': pg_config.get('user', DATABASES['default']['USER']),
            'PASSWORD': pg_config.get('password', DATABASES['default']['PASSWORD']),
            'HOST': pg_config.get('host', DATABASES['default']['HOST']),
            'PORT': pg_config.get('port', DATABASES['default']['PORT']),
        })

        # Try a fast connection probe; fall back to SQLite if unavailable
        try:
            import psycopg2
            psycopg2.connect(
                dbname=DATABASES['default']['NAME'],
                user=DATABASES['default']['USER'],
                password=DATABASES['default']['PASSWORD'],
                host=DATABASES['default']['HOST'],
                port=DATABASES['default']['PORT'],
                connect_timeout=2,
            ).close()
        except Exception as e:
            print(f"Warning: PostgreSQL unavailable, falling back to SQLite: {e}")
            DATABASES['default'] = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        
except Exception as e:
    print(f"Warning: Could not load database config: {e}")
    # Fallback MongoDB config
    MONGODB_CONFIG = {
        'uri': 'mongodb://localhost:27017/',
        'database': 'forensics'
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# CORS settings for frontend integration
# CORS fully open for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ["*"]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'forensic_backend.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'forensic_api': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB

# Custom settings for forensic application
FORENSIC_SETTINGS = {
    'MAX_CASE_SIZE': 10 * 1024 * 1024 * 1024,  # 10GB
    'SUPPORTED_IMAGE_FORMATS': ['.e01', '.dd', '.raw', '.img'],
    'EXTRACTION_TIMEOUT': 3600,  # 1 hour
    'TEMP_EXTRACTION_DIR': BASE_DIR / 'temp_extractions',
}

# Create temp directory if it doesn't exist
os.makedirs(FORENSIC_SETTINGS['TEMP_EXTRACTION_DIR'], exist_ok=True)
