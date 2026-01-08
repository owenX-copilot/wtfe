"""
Configuration settings
"""
import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    
    # Database settings (not used in this simple version)
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///blog.db')
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'blog_api.log'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
