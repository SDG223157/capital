from flask import Flask
from flask.cli import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Load environment variables
    load_dotenv()
    
    # Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    
    # Database configuration directly in __init__.py (as backup if config.py fails)
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:"
        f"{os.getenv('MYSQL_PASSWORD')}@"
        f"{os.getenv('MYSQL_HOST')}:"
        f"{os.getenv('MYSQL_PORT', '3306')}/"
        f"{os.getenv('MYSQL_DATABASE')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Register routes
    from app import routes
    app.register_blueprint(routes.main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app