"""
Flask application factory
"""
from flask import Flask
from routes import register_routes
from utils.logger import setup_logger

def create_app(config):
    """Create and configure Flask app."""
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Setup logging
    logger = setup_logger(app)
    
    # Register routes
    register_routes(app)
    
    logger.info("Blog API initialized successfully")
    return app
