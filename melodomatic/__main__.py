"""
Entry point for the program.
"""

import argparse
import time
from melodomatic import consts, reader, viz

# pylint: disable=import-outside-toplevel

class MelodomaticMain:
    """ Owns the top level managers and main run loop. """

    def __init__(self, fn):
        """ Create the default Reader, Player, and Visualizer. """
        self.filename = fn
        self.reader = reader.Reader(self.filename)
        self.set_visualizer(viz.TTYVisualizer())
        self.player = None

    def load(self):
        """ Reload the script and create a new Player. """
        self.player = self.reader.load_script(0)

    def set_visualizer(self, v):
        """ attach and initialize a viz.Visualizeer.  """
        self.visualizer = v
        if self.visualizer:
            self.visualizer.startup()

    # pylint: disable=unused-variable # for lastt, dt, etc.
    def run(self):
        """ Main run loop. """
        if not self.player.is_valid():
            if consts.VERBOSE:
                print('Ending: empty script')
            return
        self.player.startup()
        lastt = t = time.time()

        try:
            while True:
                # update time
                lastt = t
                t = time.time()
                #dt = t - lastt

                # check for a file change
                if self.reader.update(self.player.pulse):
                    # if the file has changed, build a new player and swap it in for the old one.
                    self.player = self.reader.load_script(self.player.pulse, self.player)
                    if not self.player.is_valid():
                        if consts.VERBOSE:
                            print('Ending: empty script')
                        break

                # play some music!
                if not self.player.update():
                    break

                if not consts.QUIET and self.visualizer:
                    rv = self.visualizer.update(self.player, self.reader)
                    if rv != 0:
                        break

                # wait for next pulse
                nextt = t + self.player.pulseTime
                waitt = nextt - time.time()
                if waitt > 0:
                    time.sleep(waitt)
                self.player.tick()

        except KeyboardInterrupt:
            if consts.VERBOSE:
                print('Ending: hit ^C')
        finally:
            self.player.shutdown()
            if self.visualizer:
                self.visualizer.shutdown()


def bootstrap(args, scr):
    """ Process args and start up the engine. """
    if args.verbose:
        consts.set_verbose(True)
    if args.quiet:
        consts.set_quiet(True)
    main = MelodomaticMain(args.filename)
    if consts.QUIET:
        main.set_visualizer(None)
    elif scr:
        from melodomatic import vizcurses
        main.set_visualizer(vizcurses.CursesVisualizer(scr))
    main.load()
    main.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='file containing player script')
    parser.add_argument('-q', '--quiet', dest='quiet', action='store_true', help='don\'t print out visualization junk')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', help='print extra debug spam')
    parser.add_argument('--viz', dest='viz', action='store_true', help='use fancy visualizer')
    pargs = parser.parse_args()

    try:
        if pargs.viz:
            import curses
            import locale
            locale.setlocale(locale.LC_ALL, '')
            curses.wrapper(lambda scr: bootstrap(pargs, scr))
        else:
            bootstrap(pargs, None)
    except KeyboardInterrupt:
        print('Ending: hit ^C')

    print('Goodbye.')

