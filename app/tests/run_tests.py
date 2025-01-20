# app/tests/run_tests.py

import unittest
import os
import sys

def setup_test_environment():
    """Setup the environment for testing"""
    # Get the project root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Add project root to Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        
    print(f"Test Directory: {current_dir}")
    print(f"Project Root: {project_root}")
    print(f"Python Path: {sys.path}")

def run_tests():
    """Run all tests in the test directory"""
    # Setup environment
    setup_test_environment()
    
    # Get the directory containing this file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=test_dir, pattern='test_*.py')
    
    # Run tests with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\nTest Summary:")
    print(f"Tests Run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(not success)