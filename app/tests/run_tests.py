# app/tests/run_tests.py

import unittest
import sys
import os

# Get the parent directory of 'app'
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the project root to Python path
sys.path.insert(0, project_root)

def run_tests():
    """Run all tests in the news directory"""
    # Get the directory containing the tests
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == '__main__':
    result = run_tests()
    sys.exit(not result.wasSuccessful())