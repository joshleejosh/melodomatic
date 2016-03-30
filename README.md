# MELODOMATIC

A script-controlled procedural MIDI sequencer.

### FEATURES

* MIDI output
* Control multiple voices
* Change keys/chords as the program progresses
* Cryptic scripting language to control sequences
* Hotload scripts for livecoding fun (https://youtu.be/Mvmt8FRrqK8)

### REQUIREMENTS

* A MIDI device to receive data from this program
* Mido (http://mido.readthedocs.org/)
  * Mido requires PortMIDI (http://portmedia.sourceforge.net/portmidi/)

### SCRIPT FORMAT

Melodomatic is controlled by a script file. See `melodomatic_script.txt` for notes on the data types.

### RUNNING

Melodomatic is a python module, and can be run from the command line.

```
usage: python melodomatic [-h] [-s SEED] [-q] [-v] filename

positional arguments:
  filename              File containing player data.

optional arguments:
  -h, --help            show this help message and exit
  -s SEED, --seed SEED  Seed value for random numbers.
  -q, --quiet           Don't print out visualization junk.
  -v, --verbose         Print extra debug spam.
```


### TODO

* Separate note frequency (when notes play) from duration (how long a note is held)
* Separate the pitch classes of a scale from the pitches you want to play
* Build phrases instead of plucking random notes
  * Connectors between phrases: silence, leading notes, fills, gliss?
  * Repetition?
* Better MIDIing
  * Channels
  * Aftertouch, pitchbend, etc.
  * When should we use note-off instead of note-on with velocity=0?

