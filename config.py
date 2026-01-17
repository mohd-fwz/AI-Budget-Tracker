"""
Configuration module for Budget API
Loads environment variables and provides configuration settings
"""
import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Database Configuration - SQLite (local file-based database)
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///budget.db')

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLite doesn't need connection pooling like PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }

    # AI API Configuration (Groq)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
    GROQ_MODEL = 'llama-3.3-70b-versatile'  # Updated free tier model (Dec 2024)

    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # File Upload Configuration
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size (increased for PDFs/Excel)
    ALLOWED_EXTENSIONS = {'csv', 'pdf', 'xlsx', 'xls'}

    # Session Configuration
    UPLOAD_SESSION_TIMEOUT = 3600  # 1 hour (in seconds)

    # PDF Configuration
    PDF_PASSWORD_ATTEMPTS = 3  # Maximum password attempts allowed
    PDF_MAX_PAGES = 100  # Reject PDFs with more than 100 pages

    # AI Configuration (for format detection)
    AI_FORMAT_DETECTION_ENABLED = True  # Use AI to detect columns when auto-detection fails

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @staticmethod
    def validate_config():
        """Validate that required configuration variables are set"""
        # Only validate Groq API key (optional for AI features)
        if not os.getenv('GROQ_API_KEY'):
            print("Warning: GROQ_API_KEY not set. AI features will be limited.")

        return True
