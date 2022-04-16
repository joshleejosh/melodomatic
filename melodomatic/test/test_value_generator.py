import unittest, random
from . import testhelper
from .. import consts, generators

class DummyContext:
    def __init__(self):
        self.rng = random.Random()
        self.rng.seed('SEEDS')

class ValueGeneratorTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        self.dummy = None
        testhelper.tearDown()
    def bindit(self, s):
        data = testhelper.tokenize(s)
        self.dummy = DummyContext()
        return generators.bind_generator(data, self.dummy)
    def checkit(self, f, vs):
        a = vs.split()
        for i in range(len(a)):
            self.assertEqual(next(f), a[i])

    def test_eq(self):
        f = self.bindit('BLEH')
        g = self.bindit('$SCALAR BLEH')
        self.assertEqual(f, g)
        self.assertNotEqual(f, None)
        h = self.bindit('$RANDOM BLEH')
        self.assertNotEqual(f, h)
        f = self.bindit('$wave SINE INOUT 13 0 30')
        g = self.bindit('$wave sin io 13 0 30')
        self.assertNotEqual(f, g)
        g = self.bindit('$wave SINE INOUT 13 0 30')
        self.assertEqual(f, g)

    def test_iter(self):
        g = self.bindit('$SCALAR BLEH')
        for i,v in enumerate(g):
            self.assertEqual(v, 'BLEH')
            if i > 2:
                break

    def test_bad_generator(self):
        gbind = generators.bind_generator(['$QWIJYBO', '1', '2', '3'], 'context')
        self.assertEqual(gbind.name, 'SCALAR')
        self.assertEqual(gbind.data, ['1','2','3',])
        self.assertEqual(gbind.context, 'context')

    def test_scalar(self):
        fg = self.bindit('BLEH')
        self.assertEqual(str(fg), "$SCALAR ['BLEH']")
        self.assertEqual(fg.name, 'SCALAR')
        self.assertEqual(fg.data, ['BLEH'])
        self.assertEqual(fg.context, self.dummy)

        for i in range(100):
            self.assertEqual(next(fg), 'BLEH')
        fg = self.bindit('$scAlar BNUGH')
        self.assertEqual(str(fg), "$SCALAR ['BNUGH']")
        for i in range(100):
            self.assertEqual(next(fg), 'BNUGH')

        # If you pass in a tuple instead of a list, the label reflects it.
        # It shouldn't affect processing at all (generators shouldn't modify values)
        fg = generators.bind_generator(('BORK',), DummyContext())
        self.assertEqual(str(fg), "$SCALAR ('BORK',)")

        fg = self.bindit('')
        self.assertEqual(str(fg), "$SCALAR ('1',)")
        self.checkit(fg, '1 1 1 1 1 1 1 1')
        fg = self.bindit('$sc')
        self.assertEqual(str(fg), "$SCALAR ('1',)")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_random(self):
        # bare list defualts to $RANDOM
        fg = self.bindit('FOO BAR')
        self.assertEqual(str(fg), "$RANDOM ['FOO', 'BAR']")
        self.checkit(fg, 'BAR BAR BAR FOO FOO')

        fg = self.bindit('$raNdOm FOO BAR')
        self.assertEqual(fg.name, 'RANDOM')
        self.assertEqual(fg.data, ['FOO', 'BAR'])
        self.assertEqual(fg.context, self.dummy)
        self.assertEqual(str(fg), "$RANDOM ['FOO', 'BAR']")
        self.checkit(fg, 'BAR BAR BAR FOO FOO')

        fg = self.bindit('$r')
        self.assertEqual(str(fg), "$RANDOM ('1',)")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_shuffle(self):
        fg = self.bindit('$shuffle FOO BAR BAZ QUX')
        self.assertEqual(str(fg), "$SHUFFLE ['FOO', 'BAR', 'BAZ', 'QUX']")
        self.checkit(fg, 'FOO BAR BAZ QUX BAR BAZ FOO QUX BAZ')

        fg = self.bindit('$sh FOO')
        self.assertEqual(str(fg), "$SHUFFLE ['FOO']")
        self.checkit(fg, 'FOO FOO FOO FOO FOO FOO FOO FOO FOO')

        fg = self.bindit('$sh')
        self.assertEqual(str(fg), "$SHUFFLE ('1',)")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_loop(self):
        fg = self.bindit('$loop FOO BAR BAZ QUX')
        self.assertEqual(str(fg), "$LOOP ['FOO', 'BAR', 'BAZ', 'QUX']")
        self.checkit(fg, 'FOO BAR BAZ QUX FOO BAR BAZ QUX FOO')
        fg = self.bindit('$lo FOO')
        self.assertEqual(str(fg), "$LOOP ['FOO']")
        self.checkit(fg, 'FOO FOO FOO FOO FOO FOO FOO FOO FOO')
        fg = self.bindit('$lo')
        self.assertEqual(str(fg), "$LOOP ('1',)")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_pingpong(self):
        fg = self.bindit('$pingpong FOO BAR BAZ QUX GUH')
        self.assertEqual(str(fg), "$PINGPONG ['FOO', 'BAR', 'BAZ', 'QUX', 'GUH']")
        self.checkit(fg, 'FOO BAR BAZ QUX GUH QUX BAZ BAR FOO BAR BAZ QUX GUH QUX BAZ BAR FOO BAR BAZ')
        # $pp is an alias for $pingpong
        fg = self.bindit('$pp FOO')
        self.assertEqual(str(fg), "$PP ['FOO']")
        self.checkit(fg, 'FOO FOO FOO FOO FOO FOO FOO FOO FOO')
        fg = self.bindit('$pp')
        self.assertEqual(str(fg), "$PP ('1',)")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_random_walk(self):
        fg = self.bindit('$random-walk .75 FOO BAR BAZ QUX')
        self.assertEqual(str(fg), "$RANDOM-WALK ['.75', 'FOO', 'BAR', 'BAZ', 'QUX']")
        self.checkit(fg, 'QUX QUX BAZ BAZ BAR BAZ BAR FOO BAR BAZ QUX BAZ QUX BAZ BAZ')

        # should step every time
        fg = self.bindit('$random-walk 1.0 FOO BAR BAZ QUX')
        self.assertEqual(str(fg), "$RANDOM-WALK ['1.0', 'FOO', 'BAR', 'BAZ', 'QUX']")
        self.checkit(fg, 'QUX BAZ QUX BAZ QUX BAZ BAR FOO BAR BAZ QUX BAZ QUX BAZ BAR')

        # no values: the binder thinks we're okay because there's an argument, so the function needs to check itself
        fg = self.bindit('$rw .75')
        self.assertEqual(str(fg), "$RW ['.75']")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

        # no args
        fg = self.bindit('$rw')
        self.assertEqual(str(fg), "$RW ('1',)")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

        # bad chance falls back to 1
        fg = self.bindit('$rw afqr3a A B')
        self.assertEqual(str(fg), "$RW ['afqr3a', 'A', 'B']")
        self.checkit(fg, 'B A B A B A B A B A B A B A B')
        

    def test_wave(self):
        # don't need to overtest the curve functions -- see ExpanderTest.test_curve() for that
        # just make sure the wave rises and falls correctly
        fg = self.bindit('$wave SINE INOUT 13 0 30')
        self.assertEqual(str(fg), "$WAVE ['SINE', 'INOUT', '13', '0', '30']")
        self.checkit(fg, '0 2 6 13 20 26 30 30 26 20 13 6 2 0 2 6 13 20 26 30 30 26 20 13 6 2 0 2 6 13 20')

        fg = self.bindit('$wAvE cubic in 13 0 4')
        self.assertEqual(str(fg), "$WAVE ['cubic', 'in', '13', '0', '4']")
        self.checkit(fg, '0 0 0 0 1 2 3 3 2 1 0 0 0 0 0 0 0 1 2 3 3 2 1 0 0 0 0 0 0 0 1')

        fg = self.bindit('$wa quint out 13 -1 -5')
        self.assertEqual(str(fg), "$WAVE ['quint', 'out', '13', '-1', '-5']")
        self.checkit(fg, '-1 -3 -4 -5 -5 -5 -5 -5 -5 -5 -5 -4 -3 -1 -3 -4 -5 -5 -5 -5 -5 -5 -5 -5 -4 -3 -1 -3 -4 -5 -5')

        # funtion defaults to LINEAR
        fg = self.bindit('$w asfr2q3r in 13 20 4')
        self.assertEqual(str(fg), "$WAVE ['asfr2q3r', 'in', '13', '20', '4']")
        self.checkit(fg, '20 18 15 13 10 8 5 5 8 10 13 15 18 20 18 15 13 10 8 5 5 8 10 13 15 18 20 18 15 13 10')

        # direction defaults to INOUT
        fg = self.bindit('$w sin asfr2q3r 13 3 10')
        self.assertEqual(str(fg), "$WAVE ['sin', 'asfr2q3r', '13', '3', '10']")
        self.checkit(fg, '3 3 4 5 6 8 9 9 8 6 5 4 3 3 3 4 5 6 8 9 9 8 6 5 4 3 3 3 4 5 6 ')

        # period defaults to 16
        fg = self.bindit('$w sin io asfr2q3r 3 10')
        self.assertEqual(str(fg), "$WAVE ['sin', 'io', 'asfr2q3r', '3', '10']")
        self.checkit(fg, '3 3 4 5 6 8 9 10 10 10 9 8 6 5 4 3 3 3 4 5 6 8 9 10 10 10 9 8 6 5 4')

        # min defaults to 0
        fg = self.bindit('$w sin io 13 asfr2q3r 10')
        self.assertEqual(str(fg), "$WAVE ['sin', 'io', '13', 'asfr2q3r', '10']")
        self.checkit(fg, '0 1 2 4 7 9 10 10 9 7 4 2 1 0 1 2 4 7 9 10 10 9 7 4 2 1 0 1 2 4 7')

        # max defaults to 127
        fg = self.bindit('$w sin io 13 3 asfr2q3r')
        self.assertEqual(str(fg), "$WAVE ['sin', 'io', '13', '3', 'asfr2q3r']")
        self.checkit(fg, '3 10 30 58 87 111 125 125 111 87 58 30 10 3 10 30 58 87 111 125 125 111 87 58 30 10 3 10 30 58 87')

        # missing args
        fg = self.bindit('$w sin io 13 3')
        self.assertEqual(str(fg), "$WAVE ['sin', 'io', '13', '3']")
        self.checkit(fg, '3 10 30 58 87 111 125 125 111 87 58 30 10 3 10 30 58 87 111 125 125 111 87 58 30 10 3 10 30 58 87')

        fg = self.bindit('$w sin io 13')
        self.assertEqual(str(fg), "$WAVE ['sin', 'io', '13']")
        self.checkit(fg, '0 7 27 56 86 111 125 125 111 86 56 27 7 0 7 27 56 86 111 125 125 111 86 56 27 7 0 7 27 56 86')

        fg = self.bindit('$w sin io')
        self.assertEqual(str(fg), "$WAVE ['sin', 'io']")
        self.checkit(fg, '0 5 19 39 63 88 108 122 127 122 108 88 63 39 19 5 0 5 19 39 63 88 108 122 127 122 108 88 63 39 19')

        fg = self.bindit('$w sin')
        self.assertEqual(str(fg), "$WAVE ['sin']")
        self.checkit(fg, '0 5 19 39 63 88 108 122 127 122 108 88 63 39 19 5 0 5 19 39 63 88 108 122 127 122 108 88 63 39 19')

        fg = self.bindit('$w')
        self.assertEqual(str(fg), "$WAVE ('1',)")
        self.checkit(fg, '0 16 32 48 64 79 95 111 127 111 95 79 64 48 32 16 0 16 32 48 64 79 95 111 127 111 95 79 64 48 32 ')

    def test_noise(self):
        # 0.1 is pretty noisy, to make for a more interesting test
        fg = self.bindit('$noise 0 32 0.1')
        self.assertEqual(str(fg), "$NOISE ['0', '32', '0.1']")
        self.checkit(fg, '15 15 15 15 15 16 16 16 16 16 15 15 15 15 15 16 16 16 16 16 15 13 11 8 6 5 6 8 11 15 18 20')

        # extremely noisy!
        fg = self.bindit('$noise -43 19 .99')
        self.assertEqual(str(fg), "$NOISE ['-43', '19', '.99']")
        self.checkit(fg, '-12 -12 -12 -9 -9 -12 -12 -12 -11 -11 -13 -11 -11 -11 -16 -10 -10 -10 -13 -10 -21 -20 -8 -14 -9 -10 -10 -24 -6 -10 -10 -28')

    def test_noise_bad(self):
        fg = self.bindit('$noise HOWDY DOODY TIME')
        self.assertEqual(next(fg), '0')


