"""
Utility helper functions
"""
import uuid
import hashlib
from datetime import datetime

def generate_id():
    """Generate a unique ID."""
    return str(uuid.uuid4())

def hash_password(password):
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def validate_post_data(data):
    """Validate post data structure."""
    required_fields = ['title', 'content', 'author']
    
    if not isinstance(data, dict):
        return False
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False
    
    return True

def format_timestamp(dt):
    """Format datetime to ISO string."""
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt)
