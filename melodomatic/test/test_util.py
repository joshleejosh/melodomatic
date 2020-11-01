import unittest, random
from . import testhelper
from .. import consts, util

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

    def test_splits(self):
        a = [0, 0.001, 1.0, 4, -7.6, 'banana', 2, -55, 8]
        ai = util.split_ints(a)
        self.assertEqual(ai, (0, 0, 1, 4, -7, 2, -55, 8))
        af = util.split_floats(a)
        self.assertEqual(af, (0.0, 0.001, 1.0, 4.0, -7.6, 2.0, -55.0, 8.0))

    def test_note_name(self):
        self.assertEqual(util.note_name(0), 'C0')
        self.assertEqual(util.note_name(10), 'A#0')
        self.assertEqual(util.note_name(23), 'B1')
        self.assertEqual(util.note_name(42), 'F#3')
        self.assertEqual(util.note_name(60), 'C5')
        self.assertEqual(util.note_name(71), 'B5')
        self.assertEqual(util.note_name(93), 'A7')
        self.assertEqual(util.note_name(100), 'E8')
        self.assertEqual(util.note_name(127), 'G10')
        # invalid note values, but this function doesn't care
        self.assertEqual(util.note_name(-1), 'B-1')
        self.assertEqual(util.note_name(128), 'G#10')


