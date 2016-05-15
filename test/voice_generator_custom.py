import voice, math, util


# Play whatever note I see the other voice playing, but stretch it out twice as long.
def vstretch(vo):
    voicer = vo.parameters['VOICE']
    multiplier = vo.parameters['MULTIPLIER']
    transposer = vo.parameters['TRANSPOSE']
    velocitier = vo.parameters['VELOCITY']
    while True:
        vn = voicer.next()
        if vn not in vo.player.voices:
            # don't know what to do, emit a rest
            yield voice.Note(vo.pulse, vo.player.parse_duration('1'), 1, 0)
        vf = vo.player.voices[vn]
        notef = vf.curNote
        d = notef.duration * float(multiplier.next())
        p = notef.pitch + int(transposer.next())
        v = notef.velocity + int(velocitier.next())
        v = util.clamp(v, 0, 127)
        yield voice.Note(vo.pulse, d, p, v)

voice.register_voice_generator('VSTRETCHER', vstretch, {
    'VOICE': ('X',),
    'MULTIPLIER': ('1',),
    'TRANSPOSE': ('0',),
    'VELOCITY': ('0',),
    })


