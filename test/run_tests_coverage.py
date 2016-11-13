# Run unit tests and measure code coverage.
import sys, os.path, unittest, coverage

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'melodomatic'))
import consts
# Set this to 2 for lots of debug junk. It makes reading the tests
# inconvenient, but it gives better coverage counts (since an irritatingly
# large portion of the code is verbose data dumps and extra messages).
consts.set_verbose(2)

coverer = coverage.Coverage(source=('melodomatic',))
coverer.start()

# -----------------------------------------------

loader = unittest.defaultTestLoader
suite = loader.discover(os.path.join(os.path.dirname(__file__), '..', 'melodomatic', 'test'))
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
# -----------------------------------------------

coverer.stop()
coverer.save()
coverer.report(show_missing=True)

