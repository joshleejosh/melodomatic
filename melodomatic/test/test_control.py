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
        p,c = self.bindit(':CONTROL CC .channel 3 .seed SEEDO .cid 10 .control_value $shuffle 0 48 96 127')
        q,d = self.bindit(':co CC .ch 3 .se SEEDO .cid 10 .cval $sh 0 48 96 127')
        self.assertEqual(c, d)



