from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
import logging
from app.config import Config
from flask_migrate import Migrate
from oauthlib.oauth2 import WebApplicationClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'error'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Initialize OAuth 2.0 client
    app.google_client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])

    from app.models import User
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    with app.app_context():
        # Create database tables and admin user
        try:
            db.create_all()
            logger.info("Database tables created successfully")

            # Check if admin user exists, if not create one
            admin_user = User.query.filter_by(email='admin@cfa187260.com').first()
            if not admin_user:
                admin = User(
                    email='admin@cfa187260.com',
                    username='admin',
                    first_name='Jiang',
                    last_name='Chen',
                    is_admin=True,
                    role='admin',
                    is_active=True
                )
                admin.set_password('Gern@8280')  # Set your desired password
                db.session.add(admin)
                db.session.commit()
                logger.info("Admin user created successfully!")
        except Exception as e:
            logger.error(f"Error during database initialization: {str(e)}")
            # Don't raise the error - allow the app to continue starting up

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

        # Configure SSL if in production
        if not app.debug and not app.testing:
            if app.config['PREFERRED_URL_SCHEME'] == 'https':
                app.config['SESSION_COOKIE_SECURE'] = True
                app.config['REMEMBER_COOKIE_SECURE'] = True

        @app.context_processor
        def utility_processor():
            return {
                'now': datetime.now()
            }

        # Debug: Print all registered endpoints
        logger.debug("Registered URLs:")
        for rule in app.url_map.iter_rules():
            logger.debug(f"{rule.endpoint}: {rule.rule}")

        # Error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return 'Page not found', 404

        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            return 'Internal server error', 500

    return app

# Add global exception handler
@db.event.listens_for(db.session, 'after_rollback')
def handle_after_rollback(session):
    logger.warning("Database session rollback occurred")