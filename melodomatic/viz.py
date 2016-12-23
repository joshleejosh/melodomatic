# encoding: utf-8
from collections import deque

STATUSBUFFERLEN = 200
PULSEWIDTH = 6
VOICEWIDTH = 9

# Are there any significant characters in this status that
# should trigger output, even if we're off-meter?
def should_force_print(s):
    return s[PULSEWIDTH:].replace(' ', '').replace('|', '') != ''

class Visualizer:
    def __init__(self):
        self.statusBuffer = deque(tuple(), STATUSBUFFERLEN)

    def startup(self):
        self.statusBuffer.clear()

    def shutdown(self):
        pass

    def update(self, player, reader):
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
        fmt = '%%%02dd'%PULSEWIDTH
        vs = fmt%status['pulse']
        if vk in status['voices']:
            vs += str.center(status['voices'][vk]['status'], VOICEWIDTH)
        return vs

    def status_line_controls(self, status):
        fmt = '%%%02dd'%PULSEWIDTH
        s = fmt%status['pulse']
        s += '%2s'%status['reader']
        for ck in status['controlOrder']:
            c = status['controls'][ck]
            s += str.center(c['status'], VOICEWIDTH)
        return s


class TTYVisualizer(Visualizer):
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
            print s
        return 0

