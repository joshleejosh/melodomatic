# A script containing custom generator functions for producing weird patterns.
# Load these generators by running melodomatic with the -i flag.
# Run generators_custom.melodomatic to test.

import generators

# A generator function takes in a data array (usually full of strings) and a
# Player for context. It should always yield one of the elements from the data
# array. The generator should never exhaust itself.
def alternate(data, ctx):
    i=0
    while True:
        yield data[i]
        i = (i+2)%len(data)

# Register the generator so that it can be used in scripts.
generators.register_generator('alternate', alternate)

# You can have multiple labels for the same function, if you want.
generators.register_generator('glorbnotz', alternate)


