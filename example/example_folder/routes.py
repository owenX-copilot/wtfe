"""
API routes for blog operations
"""
from flask import request, jsonify
from models import Post, Comment
from utils.helper import validate_post_data

# In-memory storage
posts = {}
comments = {}

def register_routes(app):
    """Register all API routes."""
    
    @app.route('/posts', methods=['GET'])
    def get_posts():
        """Get all posts."""
        return jsonify([post.to_dict() for post in posts.values()])
    
    @app.route('/posts', methods=['POST'])
    def create_post():
        """Create a new post."""
        data = request.json
        
        if not validate_post_data(data):
            return jsonify({'error': 'Invalid data'}), 400
        
        post = Post(
            title=data['title'],
            content=data['content'],
            author=data['author']
        )
        posts[post.id] = post
        
        return jsonify(post.to_dict()), 201
    
    @app.route('/posts/<post_id>', methods=['GET'])
    def get_post(post_id):
        """Get a specific post."""
        post = posts.get(post_id)
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        return jsonify(post.to_dict())
    
    @app.route('/posts/<post_id>/comments', methods=['POST'])
    def add_comment(post_id):
        """Add comment to a post."""
        if post_id not in posts:
            return jsonify({'error': 'Post not found'}), 404
        
        data = request.json
        comment = Comment(
            post_id=post_id,
            content=data['content'],
            author=data['author']
        )
        
        if post_id not in comments:
            comments[post_id] = []
        comments[post_id].append(comment)
        
        return jsonify(comment.to_dict()), 201
