# MELODOMATIC

A script-controlled procedural MIDI sequencer.

### FEATURES

* MIDI output
* Control multiple voices
* Change keys/chords as the program progresses
* Cryptic scripting language to control sequences
* Hotload scripts for livecoding fun:
  * https://youtu.be/lYkfFvX84JY
  * https://youtu.be/J7lHnEcG9Dg


### REQUIREMENTS

* A MIDI device to receive data from this program
* Mido (http://mido.readthedocs.org/)
  * Mido requires PortMIDI (http://portmedia.sourceforge.net/portmidi/)
* Pytweening for easing functions (https://github.com/asweigart/pytweening)


### SCRIPT FORMAT

Melodomatic is controlled by a script file that defines *voices* that play notes, and *scales* that define what notes can/should be played.

A very simple script looks something like this:
```
:scale FMaj
.root 65
.intervals 0 2 4 5 7 9 11

:voice Lead
.pitch 1 2 3 5 6 8
.duration 1 1 2
.velocity 64 72 80
```

See the example scripts in the `doc` directory for full explanations of script syntax.


### RUNNING

Melodomatic is a python module, and can be run from the command line.

```
usage: melodomatic [-h] [-q] [-v] filename

positional arguments:
  filename       file containing player script

optional arguments:
  -h, --help     show this help message and exit
  -q, --quiet    don't print out visualization junk
  -v, --verbose  print extra debug spam
```

