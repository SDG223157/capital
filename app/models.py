from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = 'news_articles'

    id = Column(Integer, primary_key=True)
    external_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500))
    content = Column(Text)
    url = Column(String(500))
    published_at = Column(DateTime)
    source = Column(String(100))
    sentiment_label = Column(String(50))
    sentiment_score = Column(Float)
    sentiment_explanation = Column(Text)
    brief_summary = Column(Text)
    key_points = Column(Text)
    market_impact_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    symbols = relationship("ArticleSymbol", back_populates="article", cascade="all, delete-orphan")
    metrics = relationship("ArticleMetric", back_populates="article", cascade="all, delete-orphan")

    # Add unique constraint for external_id
    __table_args__ = (UniqueConstraint('external_id', name='uq_news_external_id'),)

    def to_dict(self):
        return {
            'id': self.id,
            'external_id': self.external_id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'published_at': self.published_at.strftime("%Y-%m-%d %H:%M:%S") if self.published_at else None,
            'source': self.source,
            'sentiment': {
                'label': self.sentiment_label,
                'score': self.sentiment_score,
                'explanation': self.sentiment_explanation
            },
            'summary': {
                'brief': self.brief_summary,
                'key_points': self.key_points,
                'market_impact': self.market_impact_summary
            },
            'symbols': [symbol.symbol for symbol in self.symbols],
            'metrics': {
                'percentages': [m.to_dict() for m in self.metrics if m.metric_type == 'percentage'],
                'currencies': [m.to_dict() for m in self.metrics if m.metric_type == 'currency']
            },
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }

    @classmethod
    def get_by_external_id(cls, session, external_id):
        """Get article by external ID"""
        return session.query(cls).filter_by(external_id=external_id).first()

class ArticleSymbol(Base):
    __tablename__ = 'article_symbols'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news_articles.id', ondelete='CASCADE'))
    symbol = Column(String(50), index=True)

    # Relationship
    article = relationship("NewsArticle", back_populates="symbols")

    # Add unique constraint to prevent duplicate symbols for the same article
    __table_args__ = (UniqueConstraint('article_id', 'symbol', name='uq_article_symbol'),)

    def to_dict(self):
        return {
            'id': self.id,
            'article_id': self.article_id,
            'symbol': self.symbol
        }

class ArticleMetric(Base):
    __tablename__ = 'article_metrics'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('news_articles.id', ondelete='CASCADE'))
    metric_type = Column(Enum('percentage', 'currency', name='metric_type_enum'))
    value = Column(Float)
    context = Column(Text)

    # Relationship
    article = relationship("NewsArticle", back_populates="metrics")

    def to_dict(self):
        return {
            'id': self.id,
            'article_id': self.article_id,
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
        
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            'last_login': self.last_login.strftime("%Y-%m-%d %H:%M:%S") if self.last_login else None,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'role': self.role,
            'is_google_user': self.is_google_user
        }

    def __repr__(self):
        return f'<User {self.username}>'