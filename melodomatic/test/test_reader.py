import os, unittest, random, tempfile
import testhelper
import consts, generators, reader, midi

class PlayerTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()

    # Returns the path to the temp file.
    # Caller is responsible for deleting the file when done.
    def mkfile(self, scr):
        fd, fn = tempfile.mkstemp()
        fp = open(fn, 'w')
        fp.write(scr)
        fp.close()
        os.close(fd)
        return fn

    def test_file_read(self):
        fn = self.mkfile("""
                :p .bpm 108 .ppb 12 .reload_interval 12
                .badcmd
                :s S .r 58 .i 0 2 3 5 7 8 10
                :v V .p 1 3 5 .d 1 2 .v 72 84
                """)
        r = reader.Reader(fn)
        p = r.load_script(0)
        p.midi = midi.TestMidi()
        self.assertEqual(r.reloadInterval, 144)
        self.assertEqual(p.bpm, 108)
        self.assertEqual(str(p.voices['V'].parameters['VELOCITY']), '$RANDOM (\'72\', \'84\')')

        r.update(144)
        self.assertEqual(r.status, '_')

        # fake a file update
        r.filetime -= 1
        r.update(144)
        self.assertEqual(r.status, '*')
        self.assertEqual(r.reloadInterval, 144)
        self.assertEqual(p.bpm, 108)
        self.assertEqual(str(p.voices['V'].parameters['VELOCITY']), '$RANDOM (\'72\', \'84\')')

        os.remove(fn)

    def test_include(self):
        incfn = self.mkfile("""
:scale S .r 62 .i 0 2 3 5 7 9 10
                """)
        scrfn = self.mkfile("""
!include """ + incfn + """
:voice V .p 1 3 5 .d 1 2 .v 72 80
                """)

        r = reader.Reader(scrfn)
        p = r.load_script(0)
        self.assertEqual(str(p.scales['S'].root), '62')

        os.remove(incfn)
        os.remove(scrfn)

    def test_import(self):
        impfn = self.mkfile("""
import generators
# Return every other element in the data set.
def alternate(data, ctx):
    i=0
    while True:
        yield data[i]
        i = (i+2)%len(data)
generators.register_generator('alternate', alternate)
        """)
        scrfn = self.mkfile("""
!import """ + impfn + """
:scale S .r 62 .i 0 2 3 5 7 9 10
:voice V .d 1 2 .v 72 80
.p $alternate 1 2 3 4 5 6 7
                """)
        r = reader.Reader(scrfn)
        p = r.load_script(0)
        self.assertEqual(str(p.voices['V'].parameters['PITCH']),
                "$ALTERNATE ('1', '2', '3', '4', '5', '6', '7')")

        os.remove(impfn)
        os.remove(scrfn)

    def test_autocomplete_label(self):
        par = reader.Parser()
        self.assertEqual(par.autocomplete_label('.puls', ':PLAYER'), 'PULSES_PER_BEAT')
        self.assertEqual(par.autocomplete_label('puls', 'PLAYER'), 'PULSES_PER_BEAT')
        self.assertEqual(par.autocomplete_label('.puls', 'APLYER'), 'PULS')

