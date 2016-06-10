import unittest, random
import testhelper
import util

class UtilTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_is_int(self):
        self.assertTrue(util.is_int(0))
        self.assertTrue(util.is_int(1))
        self.assertTrue(util.is_int(1.0))
        self.assertTrue(util.is_int('0'))
        self.assertTrue(util.is_int('1'))
        self.assertTrue(util.is_int('+122'))
        self.assertTrue(util.is_int('-3452'))
        self.assertFalse(util.is_int('-3452.4232'))
        self.assertTrue(util.is_int(-3452.4232)) # !!!

    def test_is_float(self):
        self.assertTrue(util.is_float(0))
        self.assertTrue(util.is_float(1))
        self.assertTrue(util.is_float(1.0))
        self.assertTrue(util.is_float('0'))
        self.assertTrue(util.is_float('1'))
        self.assertTrue(util.is_float('+3464.1145'))
        self.assertTrue(util.is_float('-97302.14122'))
        self.assertTrue(util.is_float('-1.634E-2'))

