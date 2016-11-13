import unittest, random
import testhelper
import consts, generators

class ControlTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def bindit(self, scr):
        player = testhelper.mkplayer(scr)
        co = player.controls[player.controlOrder[0]]
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
        r,e = self.bindit("""
            :co CC .ch 3 .se SEEDO
            .cid 10 .cval $sh 0 49 96 127
            """)
        self.assertNotEqual(c, e)

    # .cid/.cval are unique in that you can specify them multiple times in a
    # single :control block.
    def test_multiple_cval(self):
        p,c = self.bindit("""
            :control CC .channel 3 .seed SEEDZ
            .cid 1         .control_value $wave lin io 384 0 64
            .control_id 10 .cval          $wave sin io 192 0 127
            .cid 7         # imbalanced
            """)

        self.assertEquals(c.channel, 2)
        self.assertEquals(c.rngSeed, 'SEEDZ')

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

    def test_update(self):
        p,c = self.bindit("""
            :scale S .r 60 .i 0 2 4 5 7 9 11
            :voice V .p 1 .d 4 .v 64
            :control CC .channel 1 .seed SEEDZ
            .ra 3p
            .cid 1   .cval  $wave lin io 60 0 64
            .cid 10  .cval  $wave sin io 30 0 127
            .cid 7   # imbalanced
            """)

        self.assertEqual(str(c.parameters['RATE']), '$SCALAR (\'3p\',)')

        p.update()
        self.assertEqual(len(p.midi.buffer), 3)
        # first message is the note
        self.assertEqual(p.midi.buffer[0].type, 'note_on') 
        # second message is control value 1
        self.assertEqual(p.midi.buffer[1].type, 'control_change') 
        self.assertEqual(p.midi.buffer[1].control, 1) 
        self.assertEqual(p.midi.buffer[1].value, 0) 
        # third message is control value 10
        self.assertEqual(p.midi.buffer[2].type, 'control_change') 
        self.assertEqual(p.midi.buffer[2].control, 10) 
        self.assertEqual(p.midi.buffer[2].value, 0) 
        # there was no cval for control 7, so it doesn't do anything.

        # tick through 15 control updates (update every 3p); cid 10 should be at the peak of its curve, while cid 1 should be halfway up.
        for i in xrange(45):
            p.pulse += 1
            p.update()
        self.assertEqual(len(p.midi.buffer), 33)
        self.assertEqual(p.midi.buffer[-2].type, 'control_change') 
        self.assertEqual(p.midi.buffer[-2].control, 1) 
        self.assertEqual(p.midi.buffer[-2].value, 32) 
        self.assertEqual(p.midi.buffer[-1].type, 'control_change') 
        self.assertEqual(p.midi.buffer[-1].control, 10) 
        self.assertEqual(p.midi.buffer[-1].value, 127) 

        # cid 10 should be at the far end of its curve; cid 1 should be at its peak.
        for i in xrange(45):
            p.pulse += 1
            p.update()
        #print p.midi.buffer[-2:]
        self.assertEqual(len(p.midi.buffer), 65)
        self.assertEqual(p.midi.buffer[-2].type, 'control_change') 
        self.assertEqual(p.midi.buffer[-2].control, 1) 
        self.assertEqual(p.midi.buffer[-2].value, 64) 
        self.assertEqual(p.midi.buffer[-1].type, 'control_change') 
        self.assertEqual(p.midi.buffer[-1].control, 10) 
        self.assertEqual(p.midi.buffer[-1].value, 0) 

    def test_pitchbend(self):
        p,c = self.bindit("""
            :scale S .r 60 .i 0 2 4 5 7 9 11
            :voice V .p 1 .d 4 .v 64
            :control CC .channel 1 .seed SEEDZ
            .ra 4p
            .pitchbend $wave lin io 20 32 64
            """)

        self.assertEqual(str(c.parameters['RATE']), '$SCALAR (\'4p\',)')

        p.update()
        self.assertEqual(len(p.midi.buffer), 2)
        self.assertEqual(p.midi.buffer[0].type, 'note_on') 
        self.assertEqual(p.midi.buffer[1].type, 'pitchwheel') 
        self.assertEqual(p.midi.buffer[1].pitch, 32) 

        for i in xrange(40):
            p.pulse += 1
            p.update()
        self.assertEqual(len(p.midi.buffer), 12)
        self.assertEqual(p.midi.buffer[-1].type, 'pitchwheel') 
        self.assertEqual(p.midi.buffer[-1].pitch, 64) 

        for i in xrange(40):
            p.pulse += 1
            p.update()
        self.assertEqual(len(p.midi.buffer), 24)
        self.assertEqual(p.midi.buffer[-1].type, 'pitchwheel') 
        self.assertEqual(p.midi.buffer[-1].pitch, 32) 

    def test_aftertouch_note(self):
        p,c = self.bindit("""
            :scale S .r 60 .i 0 2 4 5 7 9 11
            :voice V .p 1 .d 4 .v 64
            :control CC .channel 1 .seed SEEDZ
            .ra 4p
            .aftertouch $loop (%range 24 96 4)
            .voice V
            """)

        p.update()
        self.assertEqual(len(p.midi.buffer), 2)
        self.assertEqual(p.midi.buffer[0].type, 'note_on') 
        self.assertEqual(p.midi.buffer[1].type, 'polytouch') 
        self.assertEqual(p.midi.buffer[1].value, 24) 

        for i in xrange(36):
            p.pulse += 1
            p.update()
        self.assertEqual(len(p.midi.buffer), 11)
        self.assertEqual(p.midi.buffer[-1].type, 'polytouch') 
        self.assertEqual(p.midi.buffer[-1].value, 60) 
        for i in xrange(36):
            p.pulse += 1
            p.update()
        self.assertEqual(len(p.midi.buffer), 22)
        self.assertEqual(p.midi.buffer[-1].type, 'polytouch') 
        self.assertEqual(p.midi.buffer[-1].value, 96) 

    def test_aftertouch_channel(self):
        p,c = self.bindit("""
            :scale S .r 60 .i 0 2 4 5 7 9 11
            :voice V .p 1 .d 4 .v 64
            :control CC .channel 1 .seed SEEDZ
            .ra 4p
            .aftertouch $loop (%range 24 96 4)
            """)

        p.update()
        self.assertEqual(len(p.midi.buffer), 2)
        self.assertEqual(p.midi.buffer[0].type, 'note_on') 
        self.assertEqual(p.midi.buffer[1].type, 'aftertouch') 
        self.assertEqual(p.midi.buffer[1].value, 24) 

        for i in xrange(36):
            p.pulse += 1
            p.update()
        self.assertEqual(len(p.midi.buffer), 11)
        self.assertEqual(p.midi.buffer[-1].type, 'aftertouch') 
        self.assertEqual(p.midi.buffer[-1].value, 60) 
        for i in xrange(36):
            p.pulse += 1
            p.update()
        self.assertEqual(len(p.midi.buffer), 22)
        self.assertEqual(p.midi.buffer[-1].type, 'aftertouch') 
        self.assertEqual(p.midi.buffer[-1].value, 96) 

