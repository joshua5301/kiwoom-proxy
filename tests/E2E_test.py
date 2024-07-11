import unittest

class MockedE2ETest(unittest.TestCase):

    def test_main(self):
        import kiwoomproxy
        proxy = kiwoomproxy.Proxy()
        proxy.initialize()
        
if __name__ == '__main__':
    unittest.main()