from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'error'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')

    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.now()
        }

    return app