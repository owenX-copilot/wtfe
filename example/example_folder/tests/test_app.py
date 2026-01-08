"""
Unit tests for blog API
"""
import unittest
from app import create_app
from config import Config
from models import Post, Comment

class TestBlogAPI(unittest.TestCase):
    """Test cases for blog API."""
    
    def setUp(self):
        """Set up test client."""
        self.app = create_app(Config)
        self.client = self.app.test_client()
    
    def test_create_post(self):
        """Test creating a new post."""
        response = self.client.post('/posts', json={
            'title': 'Test Post',
            'content': 'This is a test',
            'author': 'Tester'
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)
        self.assertEqual(data['title'], 'Test Post')
    
    def test_get_posts(self):
        """Test getting all posts."""
        response = self.client.get('/posts')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)
    
    def test_invalid_post_data(self):
        """Test posting with invalid data."""
        response = self.client.post('/posts', json={
            'title': 'No content'
        })
        self.assertEqual(response.status_code, 400)

class TestModels(unittest.TestCase):
    """Test cases for data models."""
    
    def test_post_creation(self):
        """Test Post model creation."""
        post = Post('Title', 'Content', 'Author')
        self.assertIsNotNone(post.id)
        self.assertEqual(post.title, 'Title')
    
    def test_comment_creation(self):
        """Test Comment model creation."""
        comment = Comment('post123', 'Nice post!', 'Reader')
        self.assertIsNotNone(comment.id)
        self.assertEqual(comment.post_id, 'post123')

if __name__ == '__main__':
    unittest.main()
