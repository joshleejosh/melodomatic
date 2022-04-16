import os, unittest, random, tempfile, shutil
from melodomatic.test import testhelper
from melodomatic import consts, generators, reader, midi

class ReaderTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
        self.tempfi = 12345
        self.tempdirs = []

    def tearDown(self):
        while len(self.tempdirs) > 0:
            shutil.rmtree(self.tempdirs.pop())
        testhelper.tearDown()

    def nexttempfile(self):
        self.tempfi += 1
        return 't' + str(self.tempfi)

    def mkdir(self):
        dn = tempfile.mkdtemp()
        self.tempdirs.append(dn)
        return dn

    def mkfile(self, dir, scr):
        fn = os.path.join(dir, self.nexttempfile())
        with open(fn, 'w') as fp:
            fp.write(scr)
        return fn

    # ---------------------------------

    def test_file_read(self):
        tempdir = self.mkdir()
        fn = self.mkfile(tempdir, """
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

    def test_include(self):
        dir = self.mkdir()
        incfn = self.mkfile(dir, """
:scale S .r 62 .i 0 2 3 5 7 9 10
                """)
        scrfn = self.mkfile(dir, """
!include """ + incfn + """
:voice V .p 1 3 5 .d 1 2 .v 72 80
                """)

        r = reader.Reader(scrfn)
        p = r.load_script(0)
        self.assertEqual(str(p.scales['S'].root), '62')

    def test_include_relative_path(self):
        dir = self.mkdir()
        incfn = self.mkfile(dir, """
:scale S .r 62 .i 0 2 3 5 7 9 10
                """)
        incdir, incbn = os.path.split(incfn)
        scrfn = self.mkfile(dir, """
!include """ + incbn + """
:voice V .p 1 3 5 .d 1 2 .v 72 80
                """)

        r = reader.Reader(scrfn)
        p = r.load_script(0)
        self.assertEqual(str(p.scales['S'].root), '62')

    def test_autocomplete_label(self):
        par = reader.Parser()
        self.assertEqual(par.autocomplete_label('.puls', ':PLAYER'), 'PULSES_PER_BEAT')
        self.assertEqual(par.autocomplete_label('puls', 'PLAYER'), 'PULSES_PER_BEAT')
        self.assertEqual(par.autocomplete_label('.puls', 'APLYER'), 'PULS')

