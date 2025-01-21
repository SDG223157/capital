# app/tests/news/test_news_service.py

import unittest
from unittest.mock import Mock, patch
import os
from app.utils.news.news_service import NewsService

class TestNewsService(unittest.TestCase):
    def setUp(self):
        self.api_token = "test_token"
        with patch.dict('os.environ', {'APIFY_TOKEN': self.api_token}):
            self.news_service = NewsService()
        self.mock_data = [{'title': 'Test News'}]

    @patch('apify_client.ApifyClient')
    def test_get_news(self, MockApifyClient):
        # Create all the necessary mocks
        mock_dataset = Mock()
        mock_dataset.iterate_items.return_value = self.mock_data

        mock_actor = Mock()
        mock_actor.call.return_value = {"defaultDatasetId": "test_id"}

        mock_client = Mock()
        mock_client.actor.return_value = mock_actor
        mock_client.dataset.return_value = mock_dataset

        # Set up the ApifyClient mock
        MockApifyClient.return_value = mock_client

        # Make the call
        result = self.news_service.get_news("AAPL")

        # Verify the result
        self.assertEqual(result, self.mock_data)

        # Verify all the mock calls
        MockApifyClient.assert_called_once_with(self.api_token)
        mock_client.actor.assert_called_once_with("mscraper/tradingview-news-scraper")
        mock_actor.call.assert_called_once()
        mock_client.dataset.assert_called_once_with("test_id")
        mock_dataset.iterate_items.assert_called_once()

    def test_error_no_token(self):
        with patch.dict('os.environ', {}):
            with self.assertRaises(ValueError):
                NewsService()

    @patch('apify_client.ApifyClient')
    def test_error_api_call(self, MockApifyClient):
        # Setup mock to raise an exception
        mock_client = Mock()
        mock_client.actor.side_effect = Exception("API Error")
        MockApifyClient.return_value = mock_client

        # Test error handling
        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, [])

class TestNewsServiceIntegration(unittest.TestCase):
    """Integration tests for NewsService"""
    
    def setUp(self):
        self.api_token = os.getenv('APIFY_TOKEN')
        if not self.api_token:
            self.skipTest("No APIFY_TOKEN found in environment")
        self.news_service = NewsService(self.api_token)

    def test_get_news_real(self):
        """Test getting news with real API call"""
        result = self.news_service.get_news("AAPL")
        self.assertIsInstance(result, list)