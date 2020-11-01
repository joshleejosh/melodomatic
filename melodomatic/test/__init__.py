# melodomatic.test

import unittest
def run_tests():
    loader = unittest.defaultTestLoader
    suite = loader.discover('melodomatic.test')
    runner = unittest.TextTestRunner(verbosity=99)
    runner.run(suite)
