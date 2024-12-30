from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
import logging
from app.config import Config

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

    with app.app_context():
        # Register blueprints
        from app.routes import bp as main_bp
        logger.debug(f"Registering main blueprint: {main_bp.name}")
        app.register_blueprint(main_bp)

        try:
            from app.auth.routes import bp as auth_bp
            logger.debug(f"Registering auth blueprint: {auth_bp.name}")
            app.register_blueprint(auth_bp, url_prefix='/auth')
        except Exception as e:
            logger.error(f"Error registering auth blueprint: {str(e)}")
            raise

        from app.user.routes import bp as user_bp
        logger.debug(f"Registering user blueprint: {user_bp.name}")
        app.register_blueprint(user_bp, url_prefix='/user')

        @app.context_processor
        def utility_processor():
            return {
                'now': datetime.now()
            }

        # Debug: Print all registered endpoints
        logger.debug("Registered URLs:")
        for rule in app.url_map.iter_rules():
            logger.debug(f"{rule.endpoint}: {rule.rule}")

    return app