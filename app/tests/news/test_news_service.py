# app/tests/news/test_news_service.py
import unittest
from unittest.mock import Mock, patch
from app.utils.news.news_service import NewsService

class TestNewsService(unittest.TestCase):
    def setUp(self):
        self.news_service = NewsService('test_token')

    @patch('apify_client.ApifyClient')
    def test_get_news(self, mock_apify):
        # Mock data
        mock_news = [
            {"title": "Test News 1", "content": "Content 1"},
            {"title": "Test News 2", "content": "Content 2"}
        ]
        
        # Setup mock
        mock_dataset = Mock()
        mock_dataset.iterate_items.return_value = mock_news
        mock_apify.return_value.actor.return_value.call.return_value = {
            "defaultDatasetId": "test_id"
        }
        mock_apify.return_value.dataset.return_value = mock_dataset

        # Test
        result = self.news_service.get_news("AAPL")
        self.assertEqual(result, mock_news)

if __name__ == '__main__':
    unittest.main()