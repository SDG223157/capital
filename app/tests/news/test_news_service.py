# app/tests/news/test_news_service.py

import unittest
from unittest.mock import Mock, patch
import os
from app.utils.news.news_service import NewsService

class TestNewsService(unittest.TestCase):
    def setUp(self):
        """Set up test cases"""
        self.api_token = "test_token"
        # Using patch.dict for environment variables
        with patch.dict('os.environ', {'APIFY_TOKEN': self.api_token}):
            self.news_service = NewsService()

    @patch('apify_client.ApifyClient')
    def test_get_news(self, MockApifyClient):
        """Test successful news retrieval"""
        # Test data
        mock_data = [{'title': 'Test News'}]
        
        # Create mock objects
        mock_items = Mock()
        mock_items.iterate_items = Mock(return_value=mock_data)
        
        # Mock the client
        mock_client = Mock()
        mock_client.actor = Mock()
        mock_client.actor.return_value = Mock()
        mock_client.actor.return_value.call = Mock(return_value={'defaultDatasetId': 'test_id'})
        mock_client.dataset = Mock(return_value=mock_items)
        
        # Set up the mock client
        MockApifyClient.return_value = mock_client

        # Make the API call
        result = self.news_service.get_news("AAPL")

        # Verify results
        self.assertEqual(result, mock_data)
        
        # Verify mock calls
        MockApifyClient.assert_called_once_with(self.api_token)
        mock_client.actor.assert_called_once()
        mock_client.actor.return_value.call.assert_called_once_with(
            run_input={
                "symbols": ["AAPL"],
                "proxy": {"useApifyProxy": True},
                "resultsLimit": 100
            }
        )
        mock_client.dataset.assert_called_once_with('test_id')

    def test_no_api_token(self):
        """Test initialization without API token"""
        with patch.dict('os.environ', clear=True):
            with self.assertRaises(ValueError):
                NewsService()

    @patch('apify_client.ApifyClient')
    def test_api_error(self, MockApifyClient):
        """Test error handling during API call"""
        # Mock API error
        mock_client = Mock()
        mock_client.actor = Mock(side_effect=Exception("API Error"))
        MockApifyClient.return_value = mock_client

        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, [])

    @patch('apify_client.ApifyClient')
    def test_empty_response(self, MockApifyClient):
        """Test handling of empty response"""
        # Mock empty response
        mock_items = Mock()
        mock_items.iterate_items = Mock(return_value=[])
        
        mock_client = Mock()
        mock_client.actor = Mock()
        mock_client.actor.return_value = Mock()
        mock_client.actor.return_value.call = Mock(return_value={'defaultDatasetId': 'test_id'})
        mock_client.dataset = Mock(return_value=mock_items)
        
        MockApifyClient.return_value = mock_client

        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()