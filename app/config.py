import os

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:"
        f"{os.getenv('MYSQL_PASSWORD')}@"
        f"{os.getenv('MYSQL_HOST')}:"
        f"{os.getenv('MYSQL_PORT', '3306')}/"
        f"{os.getenv('MYSQL_DATABASE')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', "55315286115-8qgks57reafv5mn12h7dd7aicoq758ef.apps.googleusercontent.com")
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', "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")
    
    # OAuth endpoints
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URI = "https://www.googleapis.com/oauth2/v3/userinfo"
    
    # Server configuration
    SERVER_NAME = os.getenv('SERVER_NAME', 'jcfa187260.net')
    PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'https')
    
    # OAuth redirect URI
    GOOGLE_REDIRECT_URI = f"{PREFERRED_URL_SCHEME}://{SERVER_NAME}/auth/google/callback"
    
    # Security configuration
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # SSL configuration (if using Flask's built-in server)
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH')
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH')
    
    # Application configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # OAuth scopes
    GOOGLE_OAUTH_SCOPES = [
        'openid',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]

class DevelopmentConfig(Config):
    DEBUG = True
    SERVER_NAME = 'localhost:5000'
    PREFERRED_URL_SCHEME = 'http'
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Enable these if behind a proxy
    # PREFERRED_URL_SCHEME = 'https'
    # PROXY_FIX = True
    # PREFERRED_URL_SCHEME = 'https'

class TestingConfig(Config):
    TESTING = True
    SERVER_NAME = 'localhost:5000'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}