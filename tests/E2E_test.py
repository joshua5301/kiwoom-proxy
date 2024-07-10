import unittest

class MockedE2ETest(unittest.TestCase):

    def test_main(self):
        import kiwoom
        manager = kiwoom.Manager()
        manager.connect()
        
if __name__ == '__main__':
    unittest.main()