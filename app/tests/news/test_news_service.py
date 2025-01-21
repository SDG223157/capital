# app/tests/news/test_news_service.py

import unittest
from unittest.mock import Mock, patch
import os
from app.utils.news.news_service import NewsService

class TestNewsService(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.api_token = "test_token"
        with patch.dict('os.environ', {'APIFY_TOKEN': self.api_token}):
            self.news_service = NewsService()

    @patch('app.utils.news.news_service.ApifyClient')  # Change patch location
    def test_get_news(self, MockApifyClient):
        """Test successful news retrieval"""
        # Test data
        mock_data = [{'title': 'Test News'}]
        
        # Mock dataset
        mock_dataset = Mock()
        mock_dataset.iterate_items = Mock(return_value=mock_data)
        
        # Mock actor
        mock_actor = Mock()
        mock_actor.call = Mock(return_value={'defaultDatasetId': 'test_id'})
        
        # Mock client
        mock_client = Mock()
        mock_client.actor = Mock(return_value=mock_actor)
        mock_client.dataset = Mock(return_value=mock_dataset)
        
        # Set up the main mock
        MockApifyClient.return_value = mock_client

        # Make the API call
        result = self.news_service.get_news("AAPL")

        # Verify results
        self.assertEqual(result, mock_data)
        
        # Verify mock calls were made correctly
        MockApifyClient.assert_called_once_with(self.api_token)
        mock_client.actor.assert_called_once_with("mscraper/tradingview-news-scraper")
        mock_actor.call.assert_called_once_with(
            run_input={
                "symbols": ["AAPL"],
                "proxy": {"useApifyProxy": True},
                "resultsLimit": 100
            }
        )
        mock_client.dataset.assert_called_once_with('test_id')
        mock_dataset.iterate_items.assert_called_once()

    def test_no_api_token(self):
        """Test initialization without API token"""
        with patch.dict('os.environ', clear=True):
            with self.assertRaises(ValueError):
                NewsService()

    @patch('app.utils.news.news_service.ApifyClient')  # Change patch location
    def test_api_error(self, MockApifyClient):
        """Test error handling during API call"""
        mock_client = Mock()
        mock_client.actor = Mock(side_effect=Exception("API Error"))
        MockApifyClient.return_value = mock_client

        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, [])

    @patch('app.utils.news.news_service.ApifyClient')  # Change patch location
    def test_empty_dataset(self, MockApifyClient):
        """Test handling of empty dataset"""
        mock_dataset = Mock()
        mock_dataset.iterate_items = Mock(return_value=[])
        
        mock_actor = Mock()
        mock_actor.call = Mock(return_value={'defaultDatasetId': 'test_id'})
        
        mock_client = Mock()
        mock_client.actor = Mock(return_value=mock_actor)
        mock_client.dataset = Mock(return_value=mock_dataset)
        
        MockApifyClient.return_value = mock_client

        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()