import unittest, random
from . import testhelper
from .. import consts, generators

class PreprocessorTest(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass

    def test_macro(self):
        p = testhelper.mkplayer("""
            !define M44 44
            :s A
            .r @M44
            # macro defined in the middle of a block. as long as it's on
            # its own line, it should be fine.
            !define IMAJOR   	 .i    0 	 	2 3 5 	 	7 8 10	
            @IMAJOR

            # You can't refer to a macro inside another macro.
            !define nested .r @M44
            :scale B
            @nested
            """)
        s = p.scales['A']
        self.assertEqual(s.root, 44)
        self.assertEqual(s.intervals, (0, 2, 3, 5, 7, 8, 10))

        # bad nested macro ref will fail, root will stay at the default.
        s = p.scales['B']
        self.assertEqual(s.root, consts.DEFAULT_SCALE_ROOT)

    def test_macro_order(self):
        p = testhelper.mkplayer("""
            # Macro is defined after its use, should error
            :scale C
            .r @LATEMACRO
            !define LATEMACRO 48
            :scale D
            .r @LATEMACRO
            """)
        # out-of-order macro will fail, root will stay at the default.
        s = p.scales['C']
        self.assertEqual(s.root, consts.DEFAULT_SCALE_ROOT)
        # but the one after it will work.
        s = p.scales['D']
        self.assertEqual(s.root, 48)

    def test_macro_smoosh(self):
        p = testhelper.mkplayer("""
            # macro refs smooshed into the middle of other strings
            !define leading 7
            !define gross do
            !define grossm doXXm # this should not get processed, because @gross will go first and clobber it.
            :voice V
            .p -@leading- 1 3 5
            .v $ran@grossm 48 56 64
            """)
        v = p.voices['V']
        self.assertEqual(str(v.parameters['PITCH']), "$RANDOM ('-7-', '1', '3', '5')")
        self.assertEqual(str(v.parameters['VELOCITY']), "$RANDOM ('48', '56', '64')")

    def test_macro_expander(self):
        p = testhelper.mkplayer("""
            # Macros should be processed before expansion
            !define leading 7
            !define eval1 (%r 4 2 -1)
            :voice W
            .p $loop 1 @eval1 (%r @leading 5 -1)
            """)
        v = p.voices['W']
        self.assertEqual(str(v.parameters['PITCH']), "$LOOP ('1', '4', '3', '2', '7', '6', '5')")

    def test_multiline_macro(self):
        p = testhelper.mkplayer("""
            # Make a multi-line macro with backslashes
            !define durations \\
1 1 \\
   \\
2	\\
4    
            # whitespace after backslashes gets stripped
            !define pitches 1\\		
                3 \\   
                5 	 
            # A space will be inserted between each joined line
            !define velocities \\
48\\
60 # the macro will be collapsed to a single line, so this comment will clobber the values below \\
72 84
            :voice V
            .p @pitches
            .d @durations
            .v @velocities
            """)
        v = p.voices['V']
        self.assertEqual(str(v.parameters['PITCH']), "$RANDOM ('1', '3', '5')")
        self.assertEqual(str(v.parameters['DURATION']), "$RANDOM ('1', '1', '2', '4')")
        self.assertEqual(str(v.parameters['VELOCITY']), "$RANDOM ('48', '60')")

