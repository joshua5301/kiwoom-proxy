import sys
import unittest

class MockedE2ETest(unittest.TestCase):

    def test_main(self):
        from ..src.__main__ import main
        
if __name__ == '__main__':
    unittest.main()