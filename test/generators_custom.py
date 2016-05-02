# A script containing custom generator functions for producing weird patterns.
# Load these generators by running melodomatic with the -i flag.
# Run generators_custom.melodomatic to test.

import generators, scale, time, math

# A generator function takes in a data array (usually full of strings) and a
# Player for context. It should always yield one of the elements from the data
# array. The generator should never exhaust itself.
def alternate(data, player):
    i=0
    while True:
        yield data[i]
        i = (i+2)%len(data)

# Register the generator so that it can be used in scripts.
generators.register_generator('alternate', alternate)

# You can have multiple labels for the same function, if you want.
generators.register_generator('glorbnotz', alternate)


# A more unusual generator. Emits numbers in a sine wave stretched over a
# given range.
#
# Takes 3 arguments: period (a duration), min, and max (both numbers).
#
# Returns an int (though it's actually a string, since that's what receivers
# expect) in the range [min,max]
def sine(data, player):
    period = player.parse_duration(data[0])
    minv = float(data[1])
    maxv = float(data[2])
    rangev = (maxv - minv) / 2
    #print minv, maxv, rangev
    start = player.pulse
    i=0
    while True:
        s = math.sin((player.pulse/period)*2*math.pi)
        t = s * rangev + rangev + minv
        i = int(round(t))
        yield str(i)

generators.register_generator('sine', sine)

