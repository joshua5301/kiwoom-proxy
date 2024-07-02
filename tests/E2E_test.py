import sys
import unittest

class MockedE2ETest(unittest.TestCase):

    def test_main(self):
        from kiwoombot.start import start
        start()
        
if __name__ == '__main__':
    unittest.main()