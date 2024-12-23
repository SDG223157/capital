from flask import Flask
from flask.cli import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from app.config import Config
from app.data.data_service import DataService
from sqlalchemy import inspect
import os
import logging
from logging.handlers import RotatingFileHandler
import sys

# Initialize SQLAlchemy
db = SQLAlchemy()
# Initialize DataService
data_service = None

def setup_logging(app):
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Set up logging to file
    file_handler = RotatingFileHandler('logs/database.log', 
                                     maxBytes=10240, 
                                     backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    # Set up logging to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Database logging startup')

def create_app():
    app = Flask(__name__)
    
    # Setup logging
    setup_logging(app)
    
    # Load environment variables
    load_dotenv()
    app.logger.info('Environment variables loaded')
    
    # Config
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    
    # Log database configuration
    app.logger.info(f"Database Host: {os.getenv('MYSQL_HOST')}")
    app.logger.info(f"Database Name: {os.getenv('MYSQL_DATABASE')}")
    app.logger.info(f"Database User: {os.getenv('MYSQL_USER')}")
    app.logger.info(f"Database Port: {os.getenv('MYSQL_PORT')}")
    
    # Add new database config
    app.config.from_object(Config)
    app.logger.info('Database configuration loaded')
    
    try:
        # Initialize database
        db.init_app(app)
        app.logger.info('Database initialized successfully')
        
        # Initialize DataService
        global data_service
        data_service = DataService()
        app.logger.info('DataService initialized successfully')
        
        # Register routes
        from app import routes
        app.register_blueprint(routes.bp)
        app.logger.info('Routes registered successfully')
        
        # Create database tables
        with app.app_context():
            # Log existing tables before creation
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            app.logger.info(f"Existing tables before creation: {existing_tables}")
            
            db.create_all()
            app.logger.info('Database tables created successfully')
            
            # Log tables after creation
            updated_tables = inspector.get_table_names()
            app.logger.info(f"Tables after creation: {updated_tables}")
            
            # Log new tables created
            new_tables = set(updated_tables) - set(existing_tables)
            if new_tables:
                app.logger.info(f"Newly created tables: {new_tables}")
            
            # Log database connection test
            try:
                db.session.execute('SELECT 1')
                app.logger.info('Database connection test successful')
            except Exception as e:
                app.logger.error(f'Database connection test failed: {str(e)}')
                
    except Exception as e:
        app.logger.error(f'Error during app initialization: {str(e)}')
        raise
    
    return app