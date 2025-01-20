# app/tests/news/test_news_service.py

import unittest
from unittest.mock import Mock, patch
import os

class TestNewsService(unittest.TestCase):
    def setUp(self):
        from app.utils.news.news_service import NewsService
        self.news_service = NewsService()

    def test_service_initialization(self):
        self.assertIsNotNone(self.news_service)

    @patch('apify_client.ApifyClient')
    def test_get_news(self, mock_client):
        mock_data = [{"title": "Test News"}]
        mock_client.return_value.actor.return_value.call.return_value = {
            "defaultDatasetId": "test_id"
        }
        mock_client.return_value.dataset.return_value.iterate_items.return_value = mock_data
        
        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, mock_data)