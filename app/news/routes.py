from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.utils.analysis.news_service import NewsAnalysisService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('news', __name__, url_prefix='/news')

