import mido


class MelodomaticMidi:
    def __init__(self):
        self.midiOut = None

    def open(self):
        self.midiOut = mido.open_output()

    def close(self):
        self.midiOut.reset()
        self.midiOut.close()

    def send(self, m):
        self.midiOut.send(m)

    def note_on(self, n, v):
        self.send(mido.Message('note_on', note=n, velocity=v))

    def note_off(self, n, v):
        self.send(mido.Message('note_off', note=n, velocity=v))

class TestMidi(MelodomaticMidi):
    def __init__(self):
        MelodomaticMidi.__init__(self)
        self.buffer = []
    def open(self):
        del self.buffer[:]
    def close(self):
        del self.buffer[:]
    def send(self, m):
        self.buffer.append(m)


