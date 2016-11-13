import unittest, random
import testhelper
import consts, util

class UtilTest(unittest.TestCase):
    def setUp(self):
        self.quiet = consts.QUIET
        self.verbose = consts.VERBOSE
    def tearDown(self):
        consts.set_quiet(self.quiet)
        consts.set_verbose(self.verbose)

    def test_consts(self):
        consts.set_quiet(True)
        self.assertTrue(consts.QUIET)
        consts.set_quiet(False)
        self.assertFalse(consts.QUIET)
        consts.set_verbose(2)
        self.assertEqual(consts.VERBOSE, 2)
        consts.set_verbose(0)
        self.assertFalse(consts.VERBOSE, 0)

    def test_sign(self):
        self.assertEqual(util.sign(-3.14), -1)
        self.assertEqual(util.sign(-1), -1)
        self.assertEqual(util.sign(-0.001), -1)
        self.assertEqual(util.sign(0.0), 0)
        self.assertEqual(util.sign(0), 0)
        self.assertEqual(util.sign(3.14), 1)
        self.assertEqual(util.sign(1), 1)
        self.assertEqual(util.sign(0.001), 1)

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

