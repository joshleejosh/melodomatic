import unittest
import player, scale
import test_script

class ScaleTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_get_pitch(self):
        player = test_script.make_player(test_script.TEST_SCRIPT_SIMPLE)
        scale = player.scaler.scales['S']
        self.assertEqual(scale.root, 48)
        self.assertEqual(scale.intervals, (0,4,7))
        self.assertEqual(scale.get_pitch(0), 48)
        self.assertEqual(scale.get_pitch(1), 52)
        self.assertEqual(scale.get_pitch(2), 55)
        self.assertEqual(scale.get_pitch(-1), 55)
        try:
            self.assertEqual(scale.get_pitch(3), 55)
            self.fail('Bad sale interval index')
        except IndexError:
            pass

    def test_links(self):
        # S1: No links. scale should always link to itself.
        # S2: Explicit link to self
        script = """
            :scale S1
            44
            0 4 7
            :scale S2
            51
            0 4 7
            S2
            """
        player = test_script.make_player(script)
        s1 = player.scaler.scales['S1']
        s2 = player.scaler.scales['S2']
        self.assertEqual(s1.next_scale(), 'S1')
        self.assertEqual(s2.next_scale(), 'S2')

        # Two scales, linked to each other.
        script = """
            :scale S1
            44
            0 4 7
            S2
            :scale S2
            51
            0 4 7
            S1
            """
        player = test_script.make_player(script)
        s1 = player.scaler.scales['S1']
        s2 = player.scaler.scales['S2']
        self.assertEqual(s1.next_scale(), 'S2')
        self.assertEqual(s2.next_scale(), 'S1')

        # Random link
        script = """
            :scale S1
            44
            0 4 7
            S2 S3
            :scale S2
            51
            0 4 7
            S1 S2
            :scale S3
            51
            0 4 7
            S1 S2
            """
        player = test_script.make_player(script)
        s1 = player.scaler.scales['S1']
        s2 = player.scaler.scales['S2']
        s3 = player.scaler.scales['S3']
        for i in xrange(100):
            self.assertIn(s1.next_scale(), ('S2', 'S3'))
            self.assertIn(s2.next_scale(), ('S1', 'S2'))
            self.assertIn(s3.next_scale(), ('S1', 'S2'))

        # Bad link, should be culled at parse time.
        script = """
            :scale S1
            44
            0 4 7
            S2 Scrappy
            :scale S2
            51
            0 4 7
            S1
            """
        player = test_script.make_player(script)
        s1 = player.scaler.scales['S1']
        self.assertEqual(s1.links, ('S2',))
        for i in xrange(100):
            self.assertEqual(s1.next_scale(), 'S2')


