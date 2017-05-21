import unittest
import testhelper
import scale

class PitchCodeTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()

    def test_parse(self):
        self.assertEqual(scale.parse_degree('1'), (1, 0, 0))
        self.assertEqual(scale.parse_degree('2'), (2, 0, 0))
        self.assertEqual(scale.parse_degree('3'), (3, 0, 0))
        self.assertEqual(scale.parse_degree('8'), (8, 0, 0))
        self.assertEqual(scale.parse_degree('12+'), (12, 0, 1))
        self.assertEqual(scale.parse_degree('13-'), (13, 0, -1))
        self.assertEqual(scale.parse_degree('14+++'), (14, 0, 3))
        self.assertEqual(scale.parse_degree('15-+-+-'), (15, 0, -1))
        self.assertEqual(scale.parse_degree('-4'), (4, -1, 0))
        self.assertEqual(scale.parse_degree('---5'), (5, -3, 0))
        self.assertEqual(scale.parse_degree('++6'), (6, 2, 0))
        self.assertEqual(scale.parse_degree('+--++7'), (7, 1, 0))
        self.assertEqual(scale.parse_degree('-+--42+-+-+'), (42, -2, 1))

    def test_format(self):
        self.assertEqual(scale.format_degree( 1,  0,  0), '1')
        self.assertEqual(scale.format_degree( 2,  0,  0), '2')
        self.assertEqual(scale.format_degree( 3,  0,  0), '3')
        self.assertEqual(scale.format_degree( 8,  0,  0), '8')
        self.assertEqual(scale.format_degree(12,  0,  1), '12+')
        self.assertEqual(scale.format_degree(13,  0, -1), '13-')
        self.assertEqual(scale.format_degree(14,  0,  3), '14+++')
        self.assertEqual(scale.format_degree(15,  0, -1), '15-')
        self.assertEqual(scale.format_degree( 4, -1,  0), '-4')
        self.assertEqual(scale.format_degree( 5, -3,  0), '---5')
        self.assertEqual(scale.format_degree( 6,  2,  0), '++6')
        self.assertEqual(scale.format_degree( 7,  1,  0), '+7')
        self.assertEqual(scale.format_degree(42, -2,  1), '--42+')

    def test_bad(self):
        # the trailing '3+' gets dropped; the rest is parsed normally.
        self.assertEqual(scale.parse_degree('+1++-3+'), (1, 1, 1))
        # it gives up at the 'q', so the accidental never gets processed.
        self.assertEqual(scale.parse_degree('+q-'), (1, 1, 0))
        self.assertEqual(scale.parse_degree('+2q-'), (2, 1, 0))

    def test_parse_code(self):
        pl = testhelper.mkplayer(":scale S .r 60 .i 0 2 4 5 7 9 11")
        self.assertTrue('S' in pl.scales)
        sc = pl.scales['S']
        self.assertEqual(sc.parse_code('1'), (1, 0, 0))
        self.assertEqual(sc.parse_code('8'), (1, 1, 0))
        self.assertEqual(sc.parse_code('12+'), (5, 1, 1))
        self.assertEqual(sc.parse_code('13-'), (6, 1, -1))
        self.assertEqual(sc.parse_code('23-+-+--'), (2, 3, -2))
        self.assertEqual(sc.parse_code('-8'), (1, 0, 0))
        self.assertEqual(sc.parse_code('-3--'), (3, -1, -2))
        self.assertEqual(sc.parse_code('--11++'), (4, -1, 2))
        self.assertEqual(sc.parse_code('--5+-+'), (5, -2, 1))

    def test_parse_code_chromatic(self):
        pl = testhelper.mkplayer(":scale S .r 60 .i 0 1 2 3 4 5 6 7 8 9 10 11")
        self.assertTrue('S' in pl.scales)
        sc = pl.scales['S']
        self.assertEqual(sc.parse_code('1'), (1, 0, 0))
        self.assertEqual(sc.parse_code('8'), (8, 0, 0))
        self.assertEqual(sc.parse_code('12+'), (12, 0, 1))
        self.assertEqual(sc.parse_code('13-'), (1, 1, -1))
        self.assertEqual(sc.parse_code('23-+-+--'), (11, 1, -2))
        self.assertEqual(sc.parse_code('41'), (5, 3, 0))
        self.assertEqual(sc.parse_code('-8'), (8, -1, 0))
        self.assertEqual(sc.parse_code('-13'), (1, 0, 0))
        self.assertEqual(sc.parse_code('-3--'), (3, -1, -2))
        self.assertEqual(sc.parse_code('--15++'), (3, -1, 2))
        self.assertEqual(sc.parse_code('--5+-+'), (5, -2, 1))

    def test_join_degree(self):
        pl = testhelper.mkplayer(":scale S .r 60 .i 0 2 4 5 7 9 11")
        self.assertTrue('S' in pl.scales)
        sc = pl.scales['S']
        self.assertEqual(sc.join_degree(1, 0), 0)
        self.assertEqual(sc.join_degree(1, 1), 7)
        self.assertEqual(sc.join_degree(5, 1), 11)
        self.assertEqual(sc.join_degree(6, 1), 12)
        self.assertEqual(sc.join_degree(2, 3), 22)
        self.assertEqual(sc.join_degree(3, -1), -5)
        self.assertEqual(sc.join_degree(4, -1), -4)
        self.assertEqual(sc.join_degree(5, -2), -10)
        self.assertEqual(sc.join_degree(7, -3), -15)

    def test_split_degree(self):
        pl = testhelper.mkplayer(":scale S .r 60 .i 0 2 4 5 7 9 11")
        sc = pl.scales['S']
        self.assertEqual(sc.split_degree(0), (1, 0))
        self.assertEqual(sc.split_degree(7), (1, 1))
        self.assertEqual(sc.split_degree(11), (5, 1))
        self.assertEqual(sc.split_degree(12), (6, 1))
        self.assertEqual(sc.split_degree(22), (2, 3))
        self.assertEqual(sc.split_degree(-5), (3, -1))
        self.assertEqual(sc.split_degree(-4), (4, -1))
        self.assertEqual(sc.split_degree(-10), (5, -2))
        self.assertEqual(sc.split_degree(-15), (7, -3))

    def test_incr_degree(self):
        pl = testhelper.mkplayer(":scale S .r 60 .i 0 2 4 5 7 9 11")
        sc = pl.scales['S']
        self.assertEqual(sc.incr_degree('1', 4), '5')
        self.assertEqual(sc.incr_degree('3', 7), '+3')
        self.assertEqual(sc.incr_degree('+4', 16), '+++6')
        self.assertEqual(sc.incr_degree('1', -1), '-7')
        self.assertEqual(sc.incr_degree('5', -7), '-5')
        self.assertEqual(sc.incr_degree('+3', -16), '-1')

    def test_degree_distance(self):
        pl = testhelper.mkplayer(":scale S .r 60 .i 0 2 4 5 7 9 11")
        sc = pl.scales['S']
        self.assertEqual(sc.degree_distance('1', '5'), 4)
        self.assertEqual(sc.degree_distance('3', '+3'), 7)
        self.assertEqual(sc.degree_distance('+4', '+++6'), 16)
        self.assertEqual(sc.degree_distance('1', '-7'), -1)
        self.assertEqual(sc.degree_distance('5', '-5'), -7)
        self.assertEqual(sc.degree_distance('+3', '-1'), -16)

        # TODO: this doesn't know how to deal with fractions or accidentals
        self.assertEqual(sc.degree_distance('1', '5-'), 4)
        self.assertEqual(sc.degree_distance('1', '-7+'), -1)


    def test_join_degree_chromatic(self):
        pl = testhelper.mkplayer(":scale S .r 60 .i 0 1 2 3 4 5 6 7 8 9 10 11")
        self.assertTrue('S' in pl.scales)
        sc = pl.scales['S']
        self.assertEqual(sc.join_degree(1, 0), 0)
        self.assertEqual(sc.join_degree(1, 1), 12)
        self.assertEqual(sc.join_degree(5, 1), 16)
        self.assertEqual(sc.join_degree(6, 1), 17)
        self.assertEqual(sc.join_degree(2, 3), 37)
        self.assertEqual(sc.join_degree(3, -1), -10)
        self.assertEqual(sc.join_degree(4, -1), -9)
        self.assertEqual(sc.join_degree(5, -2), -20)

    def test_degree_to_pitch(self):
        pl = testhelper.mkplayer(":scale S .r 60 .i 0 2 4 5 7 9 11")
        self.assertTrue('S' in pl.scales)
        sc = pl.scales['S']
        self.assertEqual(sc.degree_to_pitch('1'), 60)
        self.assertEqual(sc.degree_to_pitch('8'), 72)
        self.assertEqual(sc.degree_to_pitch('12+'), 80)
        self.assertEqual(sc.degree_to_pitch('13-'), 80)
        self.assertEqual(sc.degree_to_pitch('23-+-+--'), 96)
        self.assertEqual(sc.degree_to_pitch('-8'), 60)
        self.assertEqual(sc.degree_to_pitch('-3--'), 50)
        self.assertEqual(sc.degree_to_pitch('--11++'), 55)
        self.assertEqual(sc.degree_to_pitch('+---+-5+-+'), 44)

