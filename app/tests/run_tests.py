# app/tests/run_tests.py
import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests():
    # Get all tests from the news directory
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'news')
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    run_tests()