"""
This module should be the only one that directly talks to a MIDI interface.
"""

import mido


class MelodomaticMidi:
    """
    I am responsible for owning the MIDI connection and sending messages down the pipe.
    """

    def __init__(self):
        """ Initialize. """
        self.midiOut = None

    def is_open(self):
        """ Returns True if we have an open port. """
        return self.midiOut is not None

    # pylint: disable=no-member # false positive on mido.open_output
    def open(self, port):
        """ Create and open the MIDI connection. """
        if port:
            self.midiOut = mido.open_output(port)
        else:
            self.midiOut = mido.open_output()

    def close(self):
        """ Close and destroy the MIDI connection. """
        if self.midiOut:
            self.midiOut.reset()
            self.midiOut.close()
            self.midiOut = None

    def send(self, m):
        """ Sends a full message to the MIDI interface. """
        self.midiOut.send(m)

    def note_on(self, ch, n, v):
        """ Format and relay a Note On message. """
        self.send(mido.Message('note_on', channel=ch, note=n, velocity=v))

    def note_off(self, ch, n, v):
        """ Format and relay a Note Off message. """
        self.send(mido.Message('note_off', channel=ch, note=n, velocity=v))

    def control(self, ch, cid, v):
        """ Format and relay a Control Change message. """
        self.send(mido.Message('control_change', channel=ch, control=cid, value=v))

    # value is in range [-8192,+8191]
    def pitchbend(self, ch, p):
        """ Format and relay a pitch bend ("pitchwheel") message. """
        self.send(mido.Message('pitchwheel', channel=ch, pitch=p))

    def aftertouch_channel(self, ch, v):
        """ Format and relay a channel-level aftertouch ("aftertouch") message. """
        self.send(mido.Message('aftertouch', channel=ch, value=v))

    def aftertouch_note(self, ch, n, v):
        """ Format and relay a note-level aftertouch ("polytouch") message. """
        self.send(mido.Message('polytouch', channel=ch, note=n, value=v))

class TestMidi(MelodomaticMidi):
    """
    Mock implementation of MelodomaticMidi for testing.

    Each message is simply added to a buffer for inspection.
    """
    def __init__(self):
        MelodomaticMidi.__init__(self)
        self.buffer = []
        self.opened = False
    def is_open(self):
        return self.opened
    def open(self, port):
        del self.buffer[:]
        self.opened = True
    def close(self):
        del self.buffer[:]
        self.opened = False
    def send(self, m):
        self.buffer.append(m)

