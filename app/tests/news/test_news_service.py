# app/tests/news/test_news_service.py

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
from app.utils.news.news_service import NewsService

class TestNewsService(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.api_token = "test_token"
        # Set up environment variable
        os.environ['APIFY_TOKEN'] = self.api_token
        self.news_service = NewsService()
        self.mock_data = [{'title': 'Test News'}]

    def tearDown(self):
        """Clean up after tests"""
        if 'APIFY_TOKEN' in os.environ:
            del os.environ['APIFY_TOKEN']

    @patch('apify_client.ApifyClient')
    def test_get_news(self, MockApifyClient):
        """Test successful news retrieval"""
        # Create mock objects
        mock_dataset = MagicMock()
        mock_dataset.iterate_items.return_value = self.mock_data

        mock_actor = MagicMock()
        mock_actor.call.return_value = {'defaultDatasetId': 'test_id'}

        mock_client = MagicMock()
        mock_client.actor.return_value = mock_actor
        mock_client.dataset.return_value = mock_dataset

        # Set up the main mock
        MockApifyClient.return_value = mock_client

        # Make the API call
        result = self.news_service.get_news("AAPL")

        # Verify results
        self.assertEqual(result, self.mock_data)

        # Verify the mock calls
        mock_client.actor.assert_called_once_with("mscraper/tradingview-news-scraper")
        mock_actor.call.assert_called_once()
        mock_client.dataset.assert_called_once_with('test_id')
        mock_dataset.iterate_items.assert_called_once()

    def test_no_api_token(self):
        """Test initialization without API token"""
        if 'APIFY_TOKEN' in os.environ:
            del os.environ['APIFY_TOKEN']
        with self.assertRaises(ValueError):
            NewsService()

    @patch('apify_client.ApifyClient')
    def test_api_error(self, MockApifyClient):
        """Test API error handling"""
        mock_client = MagicMock()
        mock_client.actor.side_effect = Exception("API Error")
        MockApifyClient.return_value = mock_client

        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()