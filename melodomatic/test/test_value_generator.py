import unittest, random
import testhelper
import consts, generators

class DummyContext:
    def __init__(self):
        self.rng = random.Random()
        self.rng.seed('SEEDS')

class ValueGeneratorTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def tokenize(self, s):
        s = s.replace('(',' ( ').replace(')', ' ) ')
        return s.strip().split()
    def bindit(self, s):
        data = self.tokenize(s)
        return generators.bind_generator(data, DummyContext())
    def checkit(self, f, vs):
        a = vs.split()
        for i in xrange(len(a)):
            self.assertEqual(f.next(), a[i])

    def test_scalar(self):
        fg, label = self.bindit('BLEH')
        self.assertEqual(label, "$SCALAR ['BLEH']")
        for i in xrange(100):
            self.assertEqual(fg.next(), 'BLEH')
        fg, label = self.bindit('$scAlar BNUGH')
        self.assertEqual(label, "$SCALAR ['BNUGH']")
        for i in xrange(100):
            self.assertEqual(fg.next(), 'BNUGH')

        # If you pass in a tuple instead of a list, the label reflects it.
        # It shouldn't affect processing at all (generators shouldn't modify values)
        fg, label = generators.bind_generator(('BORK',), DummyContext())
        self.assertEqual(label, "$SCALAR ('BORK',)")

        fg, label = self.bindit('')
        self.assertEqual(label, "$SCALAR ['1']")
        self.checkit(fg, '1 1 1 1 1 1 1 1')
        fg, label = self.bindit('$sc')
        self.assertEqual(label, "$SCALAR ['1']")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_random(self):
        # bare list defualts to $RANDOM
        fg, label = self.bindit('FOO BAR')
        self.assertEqual(label, "$RANDOM ['FOO', 'BAR']")
        self.checkit(fg, 'FOO FOO BAR BAR FOO')

        fg, label = self.bindit('$raNdOm FOO BAR')
        self.assertEqual(label, "$RANDOM ['FOO', 'BAR']")
        self.checkit(fg, 'FOO FOO BAR BAR FOO')

        fg, label = self.bindit('$r')
        self.assertEqual(label, "$RANDOM ['1']")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_shuffle(self):
        fg, label = self.bindit('$shuffle FOO BAR BAZ QUX')
        self.assertEqual(label, "$SHUFFLE ['FOO', 'BAR', 'BAZ', 'QUX']")
        self.checkit(fg, 'BAZ QUX FOO BAR FOO QUX BAR BAZ FOO')

        fg, label = self.bindit('$sh FOO')
        self.assertEqual(label, "$SHUFFLE ['FOO']")
        self.checkit(fg, 'FOO FOO FOO FOO FOO FOO FOO FOO FOO')

        fg, label = self.bindit('$sh')
        self.assertEqual(label, "$SHUFFLE ['1']")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_loop(self):
        fg, label = self.bindit('$loop FOO BAR BAZ QUX')
        self.assertEqual(label, "$LOOP ['FOO', 'BAR', 'BAZ', 'QUX']")
        self.checkit(fg, 'FOO BAR BAZ QUX FOO BAR BAZ QUX FOO')
        fg, label = self.bindit('$lo FOO')
        self.assertEqual(label, "$LOOP ['FOO']")
        self.checkit(fg, 'FOO FOO FOO FOO FOO FOO FOO FOO FOO')
        fg, label = self.bindit('$lo')
        self.assertEqual(label, "$LOOP ['1']")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_pingpong(self):
        fg, label = self.bindit('$pingpong FOO BAR BAZ QUX GUH')
        self.assertEqual(label, "$PINGPONG ['FOO', 'BAR', 'BAZ', 'QUX', 'GUH']")
        self.checkit(fg, 'FOO BAR BAZ QUX GUH QUX BAZ BAR FOO BAR BAZ QUX GUH QUX BAZ BAR FOO BAR BAZ')
        # $pp is an alias for $pingpong
        fg, label = self.bindit('$pp FOO')
        self.assertEqual(label, "$PP ['FOO']")
        self.checkit(fg, 'FOO FOO FOO FOO FOO FOO FOO FOO FOO')
        fg, label = self.bindit('$pp')
        self.assertEqual(label, "$PP ['1']")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

    def test_random_walk(self):
        fg, label = self.bindit('$random-walk .75 FOO BAR BAZ QUX')
        self.assertEqual(label, "$RANDOM-WALK ['.75', 'FOO', 'BAR', 'BAZ', 'QUX']")
        self.checkit(fg, 'BAR BAZ BAR BAR BAZ QUX BAZ BAZ BAZ BAZ BAZ BAZ BAR BAR BAZ')

        # should step every time
        fg, label = self.bindit('$random-walk 1.0 FOO BAR BAZ QUX')
        self.assertEqual(label, "$RANDOM-WALK ['1.0', 'FOO', 'BAR', 'BAZ', 'QUX']")
        self.checkit(fg, 'BAR BAZ BAR FOO BAR BAZ QUX BAZ QUX BAZ BAR BAZ QUX BAZ BAR')

        # no values: the binder thinks we're okay because there's an argument, so the function needs to check itself
        fg, label = self.bindit('$rw .75')
        self.assertEqual(label, "$RW ['.75']")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

        # no args
        fg, label = self.bindit('$rw')
        self.assertEqual(label, "$RW ['1']")
        self.checkit(fg, '1 1 1 1 1 1 1 1')

        # bad chance falls back to 1
        fg, label = self.bindit('$rw afqr3a A B')
        self.assertEqual(label, "$RW ['afqr3a', 'A', 'B']")
        self.checkit(fg, 'A B A B A B A B A B A B A B A')

    def test_wave(self):
        # don't need to overtest the curve functions -- see ExpanderTest.test_curve() for that
        # just make sure the wave rises and falls correctly
        fg, label = self.bindit('$wave SINE INOUT 13 0 30')
        self.assertEqual(label, "$WAVE ['SINE', 'INOUT', '13', '0', '30']")
        self.checkit(fg, '0 2 6 13 20 26 30 30 26 20 13 6 2 0 2 6 13 20 26 30 30 26 20 13 6 2 0 2 6 13 20')

        fg, label = self.bindit('$wAvE cubic in 13 0 4')
        self.assertEqual(label, "$WAVE ['cubic', 'in', '13', '0', '4']")
        self.checkit(fg, '0 0 0 0 1 2 3 3 2 1 0 0 0 0 0 0 0 1 2 3 3 2 1 0 0 0 0 0 0 0 1')

        fg, label = self.bindit('$wa quint out 13 -1 -5')
        self.assertEqual(label, "$WAVE ['quint', 'out', '13', '-1', '-5']")
        self.checkit(fg, '-1 -3 -4 -5 -5 -5 -5 -5 -5 -5 -5 -4 -3 -1 -3 -4 -5 -5 -5 -5 -5 -5 -5 -5 -4 -3 -1 -3 -4 -5 -5')

        # funtion defaults to LINEAR
        fg, label = self.bindit('$w asfr2q3r in 13 20 4')
        self.assertEqual(label, "$WAVE ['asfr2q3r', 'in', '13', '20', '4']")
        self.checkit(fg, '20 18 15 13 10 8 5 5 8 10 13 15 18 20 18 15 13 10 8 5 5 8 10 13 15 18 20 18 15 13 10')

        # direction defaults to INOUT
        fg, label = self.bindit('$w sin asfr2q3r 13 3 10')
        self.assertEqual(label, "$WAVE ['sin', 'asfr2q3r', '13', '3', '10']")
        self.checkit(fg, '3 3 4 5 6 8 9 9 8 6 5 4 3 3 3 4 5 6 8 9 9 8 6 5 4 3 3 3 4 5 6 ')

        # period defaults to 16
        fg, label = self.bindit('$w sin io asfr2q3r 3 10')
        self.assertEqual(label, "$WAVE ['sin', 'io', 'asfr2q3r', '3', '10']")
        self.checkit(fg, '3 3 4 5 7 8 9 10 10 10 9 8 7 5 4 3 3 3 4 5 7 8 9 10 10 10 9 8 7 5 4')

        # min defaults to 0
        fg, label = self.bindit('$w sin io 13 asfr2q3r 10')
        self.assertEqual(label, "$WAVE ['sin', 'io', '13', 'asfr2q3r', '10']")
        self.checkit(fg, '0 1 2 4 7 9 10 10 9 7 4 2 1 0 1 2 4 7 9 10 10 9 7 4 2 1 0 1 2 4 7')

        # max defaults to 127
        fg, label = self.bindit('$w sin io 13 3 asfr2q3r')
        self.assertEqual(label, "$WAVE ['sin', 'io', '13', '3', 'asfr2q3r']")
        self.checkit(fg, '3 10 30 58 87 111 125 125 111 87 58 30 10 3 10 30 58 87 111 125 125 111 87 58 30 10 3 10 30 58 87')

        # missing args
        fg, label = self.bindit('$w sin io 13 3')
        self.assertEqual(label, "$WAVE ['sin', 'io', '13', '3']")
        self.checkit(fg, '3 10 30 58 87 111 125 125 111 87 58 30 10 3 10 30 58 87 111 125 125 111 87 58 30 10 3 10 30 58 87')

        fg, label = self.bindit('$w sin io 13')
        self.assertEqual(label, "$WAVE ['sin', 'io', '13']")
        self.checkit(fg, '0 7 27 56 86 111 125 125 111 86 56 27 7 0 7 27 56 86 111 125 125 111 86 56 27 7 0 7 27 56 86')

        fg, label = self.bindit('$w sin io')
        self.assertEqual(label, "$WAVE ['sin', 'io']")
        self.checkit(fg, '0 5 19 39 63 88 108 122 127 122 108 88 63 39 19 5 0 5 19 39 63 88 108 122 127 122 108 88 63 39 19')

        fg, label = self.bindit('$w sin')
        self.assertEqual(label, "$WAVE ['sin']")
        self.checkit(fg, '0 5 19 39 63 88 108 122 127 122 108 88 63 39 19 5 0 5 19 39 63 88 108 122 127 122 108 88 63 39 19')

        fg, label = self.bindit('$w')
        self.assertEqual(label, "$WAVE ['1']")
        self.checkit(fg, '0 16 32 48 64 79 95 111 127 111 95 79 64 48 32 16 0 16 32 48 64 79 95 111 127 111 95 79 64 48 32 ')

