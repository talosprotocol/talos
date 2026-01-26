import sys
import unittest
from talos_config.loader import ConfigurationLoader, ConfigurationError

class TestValidation(unittest.TestCase):
    def test_valid_config(self):
        loader = ConfigurationLoader()
        loader._config = {
            "config_version": "1.0",
            "global": { "env": "local" }
        }
        try:
            digest = loader.validate()
            print(f"Valid config digest: {digest}")
            self.assertTrue(len(digest) > 0)
        except Exception as e:
            self.fail(f"Validation failed for valid config: {e}")

    def test_invalid_config(self):
        loader = ConfigurationLoader()
        loader._config = {
            "config_version": "1.0",
            "global": { "env": "INVALID_ENV" }
        }
        with self.assertRaises(ConfigurationError) as cm:
            loader.validate()
        print(f"Caught expected error: {cm.exception}")


if __name__ == '__main__':
    unittest.main()
