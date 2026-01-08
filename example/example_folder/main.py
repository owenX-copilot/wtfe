"""
Simple Blog API - Main Entry Point
"""
from app import create_app
from config import Config

def main():
    """Start the blog API server."""
    app = create_app(Config)
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()
