# encoding: utf-8
"""
Interface and default implementations for visualizer output.
"""
from collections import deque

STATUSBUFFERLEN = 200

# Width of the pulse count in a formatted string.
PULSEWIDTH = 6

# Width of the voice name in a formatted string.
VOICEWIDTH = 9

def should_force_print(s):
    """
    Returns True if there significant characters in this status that should
    trigger output, even if we're off-meter.
    """
    return s[PULSEWIDTH:].replace(' ', '').replace('|', '') != ''

class Visualizer:
    """
    Interface for visualizers that display the stream of output from a Player.

    TTYVisualizer is the default implementation.
    """

    def __init__(self):
        """ Initialize resoources. """
        self.statusBuffer = deque(tuple(), STATUSBUFFERLEN)

    def startup(self):
        """ Initialize resoources. """
        self.statusBuffer.clear()

    def shutdown(self):
        """ Clean up resoources. """
        self.statusBuffer.clear()

    def update(self, player, reader):
        """ On each tick, this adds a record of the system status to the buffer. """

        status = {
                'pulse': 0,
                'reader': '',
                'scale': {},
                'voiceOrder': [],
                'voices': {},
                'controlOrder': [],
                'controls': {}
                }
        status['pulse'] = player.pulse
        status['reader'] = reader.status

        status['scale']['status'] = player.curScale.status
        status['scale']['id'] = player.curScale.id

        for vk in player.voiceOrder:
            status['voiceOrder'].append(vk)
            v = player.voices[vk]
            status['voices'][vk] = {
                    'status': v.status,
                    'note': v.curNote,
                    }

        for ck in player.controlOrder:
            status['controlOrder'].append(ck)
            c = player.controls[ck]
            status['controls'][ck] = {
                    'status': c.status,
                    }

        self.statusBuffer.append(status)
        return 0

    def status_line_main(self, status):
        """ Returns a formatted string of the current status of the system. """
        fmt = '%%%02dd'%PULSEWIDTH
        s = fmt%status['pulse']
        s += '%2s'%status['reader']

        controlStatus = ''
        if any(((status['controls'][c]['status'] != '') for c in status['controlOrder'])):
            controlStatus = '+'
        s += '%2s'%controlStatus

        s += str.center(status['scale']['status'], VOICEWIDTH)

        for vk in status['voiceOrder']:
            v = status['voices'][vk]
            s += str.center(v['status'], VOICEWIDTH)

        return s

    def status_line_voice(self, status, vk):
        """ Returns a formatted string of the current status of voices. """
        fmt = '%%%02dd'%PULSEWIDTH
        vs = fmt%status['pulse']
        if vk in status['voices']:
            vs += str.center(status['voices'][vk]['status'], VOICEWIDTH)
        return vs

    def status_line_controls(self, status):
        """ Returns a formatted string of the current status of control codes. """
        fmt = '%%%02dd'%PULSEWIDTH
        s = fmt%status['pulse']
        s += '%2s'%status['reader']
        for ck in status['controlOrder']:
            c = status['controls'][ck]
            s += str.center(c['status'], VOICEWIDTH)
        return s


class TTYVisualizer(Visualizer):
    """ Default implementation of Visualizer: continuously prints to the console. """

    def __init__(self):
        Visualizer.__init__(self)

    def startup(self):
        Visualizer.startup(self)

    # Update our half-baked visualization string and print it out.
    def update(self, player, reader):
        Visualizer.update(self, player, reader)
        status = self.statusBuffer[-1]
        s = self.status_line_main(status)

        if (player.pulse%player.visualizationWindow == 0) or should_force_print(s):
            print(s)
        return 0

