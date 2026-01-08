"""
Data models for blog posts
"""
from datetime import datetime
from utils.helper import generate_id

class Post:
    """Represents a blog post."""
    
    def __init__(self, title, content, author):
        self.id = generate_id()
        self.title = title
        self.content = content
        self.author = author
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        """Convert post to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Comment:
    """Represents a comment on a post."""
    
    def __init__(self, post_id, content, author):
        self.id = generate_id()
        self.post_id = post_id
        self.content = content
        self.author = author
        self.created_at = datetime.now()
    
    def to_dict(self):
        """Convert comment to dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'content': self.content,
            'author': self.author,
            'created_at': self.created_at.isoformat()
        }
