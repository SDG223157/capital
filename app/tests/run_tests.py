# app/tests/run_tests.py

import unittest
import os
import sys

def run_tests():
    """Run all tests in the test directory"""
    # Get the directory containing this file (tests directory)
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(tests_dir))
    sys.path.insert(0, project_root)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=tests_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(not success)