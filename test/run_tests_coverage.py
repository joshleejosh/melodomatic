# Run unit tests and measure code coverage.
# Run with -v to enable verbosity. This makes test output hard to read, but
# improves accuracy of coverage (an annoyingly significant percentage of code
# is verbose debug output).

import sys, os.path, unittest, coverage, argparse
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from melodomatic import consts
import melodomatic.test

def do_tests():
    coverer = coverage.Coverage(
            source=('melodomatic',),
            omit=('melodomatic/__main__.py',
                'melodomatic/consts.py',
                'melodomatic/midi.py',
                'melodomatic/viz.py',
                'melodomatic/vizcurses/__init__.py'))
    coverer.exclude('consts\.VERBOSE:')
    coverer.exclude('def dump\(self\):')
    coverer.start()

    melodomatic.test.run_tests()

    coverer.stop()
    coverer.save()
    print('\n\n')
    coverer.report(show_missing=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Print extra debug spam.')
    args = parser.parse_args()

    if args.verbose:
        consts.set_verbose(True)
    do_tests()

