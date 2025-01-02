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
    DEBUG = False
    TESTING = False
    # Google OAuth configuration
     # Google OAuth config
    GOOGLE_CLIENT_ID = "178454917807-ivou0uehjcamas4s4p2qsjhbf218ks43.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = "https://jcfa187260.net/auth/google/callback"  # Updated to match exactly
    SERVER_NAME = "cfa187260.biz"
    PREFERRED_URL_SCHEME = "https"
    # OAuth redirect URI
    GOOGLE_REDIRECT_URI = f"{PREFERRED_URL_SCHEME}://{SERVER_NAME}/auth/google/callback"
    
    # Security configuration
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    PROXY_FIX = True