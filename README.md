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
* Pytweening for easing functions (https://pypi.python.org/pypi/PyTweening/1.0.0 or https://github.com/asweigart/pytweening)


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
usage: python melodomatic [-h] [-q] [-v] filename

positional arguments:
  filename              File containing player script.

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           Don't print out visualization junk.
  -v, --verbose         Print extra debug spam.
```


### TODO

* On reload, diff voices and maintain them if they haven't changed.
* Separate note hold (sustain) from duration (time til next note)
* Build phrases instead of plucking random notes
  * Connectors between phrases: silence, leading notes, fills, gliss?
  * Repetition?
* noise: white (why?); 1D perlin (as a replacement for $RW?)

