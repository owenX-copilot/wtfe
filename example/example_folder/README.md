# Flask Blog API

A simple blog API built with Flask for demonstration purposes.

## Features

- RESTful API endpoints for blog posts
- SQLite database with SQLAlchemy ORM
- Configuration management
- Logging utilities
- Unit tests

## Project Structure

```
example_folder/
├── main.py          # Application entry point
├── app.py           # Flask app initialization
├── models.py        # Database models
├── routes.py        # API endpoints
├── config.py        # Configuration settings
├── utils/           # Utility modules
│   ├── helper.py    # Helper functions
│   └── logger.py    # Logging setup
└── tests/           # Unit tests
    └── test_app.py  # API tests
```

## Installation

```bash
pip install flask sqlalchemy
```

## Usage

### Run the application

```bash
python main.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

- `GET /` - Welcome message
- `GET /posts` - List all posts
- `POST /posts` - Create a new post
- `GET /posts/<id>` - Get a specific post

## Testing

```bash
python -m pytest tests/
```

## Configuration

Edit `config.py` to customize:
- Database URL
- Debug mode
- Secret key

## Dependencies

- Flask - Web framework
- SQLAlchemy - ORM for database operations

## License

MIT License - This is a demonstration project.
