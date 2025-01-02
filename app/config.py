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
     # Google OAuth config
    GOOGLE_CLIENT_ID = "55315286115-c3pfanof3pnngvrp4tmg1f78tmsuqtto.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = "http://jcfa187260.net/auth/google/callback"  # Updated to match exactly
    SERVER_NAME = "jcfa187260.net"
    PREFERRED_URL_SCHEME = "http"
    # OAuth redirect URI
    GOOGLE_REDIRECT_URI = f"{PREFERRED_URL_SCHEME}://{SERVER_NAME}/auth/google/callback"
    
    # Security configuration
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True