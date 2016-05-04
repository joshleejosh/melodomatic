# A script containing custom generator functions for producing weird patterns.
# Load these generators by running melodomatic with the -i flag.
# Run generators_custom.melodomatic to test.

import generators, math

# A more unusual generator. Emits values in a sine wave stretched over a
# given range.
#
# Takes 3 arguments: period (a duration), min, and max (both numbers).
#
# Returns an int (though it's actually a string, since that's what receivers
# expect) in the range [min,max]
def sine(data, ctx):
    period = ctx.player.parse_duration(data[0])
    minv = float(data[1])
    maxv = float(data[2])
    rangev = (maxv - minv) / 2
    #print minv, maxv, rangev
    start = ctx.player.pulse
    i=0
    while True:
        s = -math.cos((ctx.player.pulse/period)*2*math.pi)
        t = s * rangev + rangev + minv
        i = int(round(t))
        yield str(i)

generators.register_generator('sine', sine)

