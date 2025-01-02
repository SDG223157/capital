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
    
    # Additional Flask configurations can be added here
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    GOOGLE_CLIENT_ID = "55315286115-8qgks57reafv5mn12h7dd7aicoq758ef.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = "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"
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"