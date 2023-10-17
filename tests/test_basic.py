# Basic test suite
import unittest

class TestBasicFeatures(unittest.TestCase):
    def test_data_processing(self):
        from sample_feature_1 import process_data
        test_data = ["test", "data"]
        result = process_data(test_data)
        self.assertEqual(result, ["TEST", "DATA"])
    
    def test_config_validation(self):
        from sample_feature_3 import validate_config
        config = {"name": "test", "type": "agent", "endpoints": ["http://test.com"]}
        self.assertTrue(validate_config(config))

if __name__ == '__main__':
    unittest.main()