from flask import Blueprint

bp = Blueprint('news', __name__)

from app.news import routes  # Import routes after creating blueprint