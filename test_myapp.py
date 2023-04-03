import unittest
from database import get_categories
import asyncio
import requests

class TestGetCategories(unittest.TestCase):
    
    def test_get_categories(self):
        result = asyncio.run(get_categories())
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(isinstance(category, str) for category in result))

class TestFetchCategories(unittest.TestCase):
    
    def test_fetch_categories(self):
        response = requests.get('http://localhost:8000/api/categories')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertTrue(all(isinstance(category, str) for category in response.json()))