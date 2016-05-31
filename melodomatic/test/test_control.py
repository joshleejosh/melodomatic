import unittest, random
import testhelper
import consts, generators

class ControlTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def bindit(self, scr, cid=''):
        player = testhelper.mkplayer(scr)
        co = player.controls[player.controlOrder[0]]
        if cid:
            co = player.controls[cid]
        return player, co
 
    def test_eq(self):
        p,c = self.bindit("""
            :CONTROL CC .channel 3 .seed SEEDO
            .cid 10 .control_value $shuffle 0 48 96 127
            """)
        q,d = self.bindit("""
            :co CC .ch 3 .se SEEDO
            .cid 10 .cval $sh 0 48 96 127
            """)
        self.assertEqual(c, d)

    # .cid/.cval are unique in that you can specify them multiple times in a
    # single :control block.
    def test_multiple_cval(self):
        p,c = self.bindit("""
            :control CC .channel 1 .seed SEEDZ
            .cid 1         .control_value $wave lin io 384 0 64
            .control_id 10 .cval          $wave sin io 192 0 127
            .cid 7         # imbalanced
            """)

        self.assertEqual(len(c.parameters['CONTROL_ID']), 3)
        self.assertEqual(len(c.parameters['CONTROL_VALUE']), 2)
        self.assertEqual(str(c.parameters['CONTROL_ID'][0]),
                "$SCALAR ('1',)")
        self.assertEqual(str(c.parameters['CONTROL_VALUE'][0]),
                "$WAVE ('lin', 'io', '384', '0', '64')")
        self.assertEqual(str(c.parameters['CONTROL_ID'][1]),
                "$SCALAR ('10',)")
        self.assertEqual(str(c.parameters['CONTROL_VALUE'][1]),
                "$WAVE ('sin', 'io', '192', '0', '127')")


