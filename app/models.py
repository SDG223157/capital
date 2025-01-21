from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# app/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = 'news_articles'

    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    content = Column(Text)
    url = Column(String(500))
    published_at = Column(DateTime)
    source = Column(String(100))
    sentiment_label = Column(String(50))
    sentiment_score = Column(Float)
    brief_summary = Column(Text)
    key_points = Column(Text)
    market_impact_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    symbols = relationship("ArticleSymbol", back_populates="article")
    metrics = relationship("ArticleMetric", back_populates="article")

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'published_at': self.published_at.strftime("%Y-%m-%d %H:%M:%S") if self.published_at else None,
            'source': self.source,
            'sentiment_label': self.sentiment_label,
            'sentiment_score': self.sentiment_score,
            'brief_summary': self.brief_summary,
            'key_points': self.key_points,
            'market_impact_summary': self.market_impact_summary,
            'symbols': [symbol.symbol for symbol in self.symbols],
            'metrics': {
                'percentages': [m.to_dict() for m in self.metrics if m.metric_type == 'percentage'],
                'currencies': [m.to_dict() for m in self.metrics if m.metric_type == 'currency']
            }
        }

class ArticleSymbol(Base):
    __tablename__ = 'article_symbols'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'))
    symbol = Column(String(50), index=True)

    # Relationship
    article = relationship("NewsArticle", back_populates="symbols")

class ArticleMetric(Base):
    __tablename__ = 'article_metrics'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news_articles.id'))
    metric_type = Column(Enum('percentage', 'currency'))
    value = Column(Float)
    context = Column(Text)

    # Relationship
    article = relationship("NewsArticle", back_populates="metrics")

    def to_dict(self):
        return {
            'value': self.value,
            'context': self.context,
            'type': self.metric_type
        }

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')
    is_google_user = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()
        
    @property
    def is_administrator(self):
        """Check if user has admin privileges"""
        return self.is_admin or self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'