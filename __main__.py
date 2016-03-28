import argparse
import consts
from util import *
import player, reader

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='File containing player data.')
    parser.add_argument('-s', '--seed', dest='seed', action='store', help='Seed value for random numbers.')
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true', help='Don\'t print out visualization junk.')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='Print extra debug spam.')
    args = parser.parse_args()
    if args.verbose:
        consts.set_verbose(True)
    if args.quiet:
        consts.set_quiet(True)

    seed_random(args.seed)

    player = player.Player()
    reader = reader.Reader(args.filename, player)
    reader.load_script()
    player.run()

