import mido


class MelodomaticMidi:
    def __init__(self):
        self.midiOut = None

    def open(self):
        self.midiOut = mido.open_output()

    def close(self):
        if self.midiOut:
            self.midiOut.reset()
            self.midiOut.close()

    def send(self, m):
        self.midiOut.send(m)

    def note_on(self, ch, n, v):
        self.send(mido.Message('note_on', channel=ch, note=n, velocity=v))

    def note_off(self, ch, n, v):
        self.send(mido.Message('note_off', channel=ch, note=n, velocity=v))

    def control(self, ch, id, v):
        self.send(mido.Message('control_change', channel=ch, control=id, value=v))

    # value is in range [-8192,+8191]
    def pitchbend(self, ch, p):
        self.send(mido.Message('pitchwheel', channel=ch, pitch=p))

    def aftertouch_channel(self, ch, v):
        self.send(mido.Message('aftertouch', channel=ch, value=v))

    def aftertouch_note(self, ch, n, v):
        self.send(mido.Message('polytouch', channel=ch, note=n, value=v))

class TestMidi(MelodomaticMidi):
    def __init__(self):
        MelodomaticMidi.__init__(self)
        self.buffer = []
        self.opened = False
    def open(self):
        del self.buffer[:]
        self.opened = True
    def close(self):
        del self.buffer[:]
        self.opened = False
    def send(self, m):
        self.buffer.append(m)


