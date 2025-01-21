# app/tests/news/test_news_service.py

import unittest
from unittest.mock import Mock, patch
import os
from app.utils.news.news_service import NewsService

class TestNewsService(unittest.TestCase):
    @patch.dict(os.environ, {'APIFY_TOKEN': 'test_token'})
    def setUp(self):
        self.news_service = NewsService()
        self.mock_data = [{'title': 'Test News'}]

    def test_service_initialization(self):
        self.assertIsNotNone(self.news_service)

    @patch('apify_client.ApifyClient')
    def test_get_news(self, mock_apify_client):
        # Create mock dataset
        mock_dataset = Mock()
        mock_dataset.iterate_items.return_value = self.mock_data

        # Create mock client
        mock_client = Mock()
        mock_client.dataset.return_value = mock_dataset

        # Set up the actor mock
        mock_actor = Mock()
        mock_actor.call.return_value = {"defaultDatasetId": "test_dataset_id"}
        mock_client.actor.return_value = mock_actor

        # Set up the ApifyClient to return our mock client
        mock_apify_client.return_value = mock_client

        # Test the method
        result = self.news_service.get_news("AAPL")

        # Assertions
        self.assertEqual(result, self.mock_data)
        
        # Verify the correct calls were made
        mock_client.actor.assert_called_once_with("mscraper/tradingview-news-scraper")
        mock_actor.call.assert_called_once_with(
            run_input={
                "symbols": ["AAPL"],
                "proxy": {"useApifyProxy": True},
                "resultsLimit": 100
            }
        )
        mock_client.dataset.assert_called_once_with("test_dataset_id")
        mock_dataset.iterate_items.assert_called_once()

    @patch('apify_client.ApifyClient')
    def test_get_news_empty_response(self, mock_apify_client):
        # Mock empty response
        mock_dataset = Mock()
        mock_dataset.iterate_items.return_value = []
        
        mock_client = Mock()
        mock_client.dataset.return_value = mock_dataset
        mock_client.actor.return_value.call.return_value = {"defaultDatasetId": "test_id"}
        
        mock_apify_client.return_value = mock_client

        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, [])

    @patch('apify_client.ApifyClient')
    def test_get_news_error_handling(self, mock_apify_client):
        # Mock error
        mock_apify_client.return_value.actor.side_effect = Exception("API Error")
        
        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()