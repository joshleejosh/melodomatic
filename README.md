# MELODOMATIC

A script-controlled procedural MIDI sequencer.

### FEATURES

* MIDI output
* Control multiple voices
* Change keys/chords as the program progresses
* Cryptic scripting language to control sequences
* Hotloading scripts for livecoding fun

### REQUIREMENTS

* A MIDI device
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

* Macros
* More error handling
* Separate note frequency (when notes play) from duration (how long a note is held)
* Option to double up voices
* Static sequences/loops
* Build phrases instead of plucking random notes
* links between phrases: silence, leading notes, fills, gliss?
* Repetition?
* Better MIDIing
  * Channels
  * Aftertouch, pitchbend, etc.



