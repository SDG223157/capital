# app/tests/news/test_news_service.py

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from app.utils.news.news_service import NewsService

class TestNewsService(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.api_token = os.getenv('APIFY_TOKEN')
        if not self.api_token:
            self.skipTest("APIFY_TOKEN not set in environment")
        self.news_service = NewsService(self.api_token)
        self.mock_data = [{'title': 'Test News'}]

    @patch('apify_client.client.ApifyClient')  # Patch the actual client path
    def test_get_news(self, MockApifyClient):
        """Test successful news retrieval"""
        # Create mock chain
        mock_dataset = MagicMock()
        mock_dataset.iterate_items.return_value = self.mock_data

        mock_actor = MagicMock()
        mock_actor.call.return_value = {'defaultDatasetId': 'test_id'}

        mock_client = MagicMock()
        mock_client.actor.return_value = mock_actor
        mock_client.dataset.return_value = mock_dataset

        # Set up the ApifyClient mock
        MockApifyClient.return_value = mock_client

        # Call the method
        result = self.news_service.get_news("AAPL")

        # Assertions
        self.assertEqual(result, self.mock_data)
        mock_client.actor.assert_called_once_with("mscraper/tradingview-news-scraper")
        mock_actor.call.assert_called_once()
        mock_client.dataset.assert_called_once_with('test_id')
        mock_dataset.iterate_items.assert_called_once()

    def test_no_api_token(self):
        """Test initialization without API token"""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                NewsService()

    @patch('apify_client.client.ApifyClient')
    def test_api_error(self, MockApifyClient):
        """Test API error handling"""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.actor.side_effect = Exception("API Error")
        MockApifyClient.return_value = mock_client

        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()