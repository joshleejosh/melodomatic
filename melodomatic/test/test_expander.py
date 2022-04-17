import unittest
from . import testhelper
from .. import expanders

class ExpanderTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def doit(self, s):
        a = testhelper.tokenize(s)
        return expanders.expand_list(a)

    def test_bare(self):
        tlist = self.doit('FOO')
        self.assertEqual(tlist, ('FOO',))
        tlist = self.doit('$guh 2 Q a28 !#7@ 6 7 8')
        self.assertEqual(tlist, ('$guh','2','Q','a28','!#7@','6','7','8'))

    def test_simple_parentheses(self):
        tlist = self.doit('A (B C D) (E F (G)) (H (I J) (K L) M) N')
        self.assertEqual(tlist, ('A','B','C','D','E','F','G','H','I','J','K','L','M','N'))
        tlist = self.doit('()')
        self.assertEqual(tlist, ())

        # unclosed parentheis: don't care
        tlist = self.doit('A (B C D) (E F (G)')
        self.assertEqual(tlist, ('A','B','C','D','E','F','G'))

        # stray close: drop everything after the last close
        tlist = self.doit('A (B C D) E) F')
        self.assertEqual(tlist, ('A','B','C','D', 'E'))

    def test_list(self):
        tlist = self.doit('%list A (B C D) (%li E F (G)) (%l H (%list I J) (K L) M) N')
        self.assertEqual(tlist, ('A','B','C','D','E','F','G','H','I','J','K','L','M','N'))
        tlist = self.doit('%list')
        self.assertEqual(tlist, ())

    def test_xerox(self):
        tlist = self.doit('%xerox 3 QRS')
        self.assertEqual(tlist, ('QRS', 'QRS', 'QRS'))
        tlist = self.doit('%x 3 X Y Z')
        self.assertEqual(tlist, ('X', 'Y', 'Z', 'X', 'Y', 'Z', 'X', 'Y', 'Z'))

        # oops, swapped count and value
        tlist = self.doit('%xErOx QRS 3')
        self.assertEqual(tlist, ('3',))

        # Bad command gets replaced with LIST
        tlist = self.doit('%xeroxA B C D')
        self.assertEqual(tlist, ('B','C','D'))

    def test_range(self):
        # %range is inclusive of min and max
        tlist = self.doit('%range 0 4')
        self.assertEqual(tlist, ('0', '1', '2', '3', '4'))

        # min and max are reversed
        tlist = self.doit('%Ran 3 -3')
        self.assertEqual(tlist, ('-3', '-2', '-1', '0', '1', '2', '3'))

        # step
        tlist = self.doit('%ra 11 19 4')
        self.assertEqual(tlist, ('11', '15', '19'))

        # negative step
        tlist = self.doit('%r 4 2 -1')
        self.assertEqual(tlist, ('4', '3', '2'))

        # edges
        tlist = self.doit('%r 3 3 -1')
        self.assertEqual(tlist, ('3',))
        tlist = self.doit('%r -3 -3 1')
        self.assertEqual(tlist, ('-3',))
        tlist = self.doit('%r 3 4 1')
        self.assertEqual(tlist, ('3', '4'))
        tlist = self.doit('%r 4 3 -1')
        self.assertEqual(tlist, ('4', '3'))

        # swapped + negative step + uneven ending:
        # first step is guaranteed to be min/max
        # last value is not guaranteed to be min/max if the step is uneven
        tlist = self.doit('%r 7 21 -3')
        self.assertEqual(tlist, ('21', '18', '15', '12', '9'))

        # bad values
        # min and max default to 0.
        tlist = self.doit('%r Funky Cold Medina')
        self.assertEqual(tlist, ('0',))

        # Fails immediately on the first bad value.
        tlist = self.doit('%r Funky 3 Medina')
        self.assertEqual(tlist, ('0',))

        # If min is set and it fails on max, swapping kicks in and we get 0-3.
        # No floats
        tlist = self.doit('%r 3 3.14159 Medina')
        self.assertEqual(tlist, ('0', '1', '2', '3',))

        # step defaults to 1.
        tlist = self.doit('%r 3 5 3.14')
        self.assertEqual(tlist, ('3','4','5'))

        # step cannot be 0, will get turned into 1
        tlist = self.doit('%r 3 5 0')
        self.assertEqual(tlist, ('3','4','5'))

    def test_crange(self):
        tlist = self.doit('%crange 2 4 1')
        self.assertEqual(tlist, ('0', '1', '2', '3', '4'))

        # step, odd range
        tlist = self.doit('%crange 12 9 3')
        self.assertEqual(tlist, ('9', '12', '15',))

        # negative step
        tlist = self.doit('%crange 2 4 -1')
        self.assertEqual(tlist, ('4', '3', '2', '1', '0'))

        # negative spread
        tlist = self.doit('%crange 23 -8 2')
        self.assertEqual(tlist, ('19', '21', '23', '25', '27'))
        tlist = self.doit('%crange 23 -8 -2')
        self.assertEqual(tlist, ('27', '25', '23', '21', '19'))

        # 0 range
        tlist = self.doit('%cr 12 0 3')
        self.assertEqual(tlist, ('12',))

        # 0 step
        tlist = self.doit('%cr 12 4 0')
        self.assertEqual(tlist, ('10', '11', '12', '13', '14'))

        # bad values
        tlist = self.doit('%cr Funky Cold Medina')
        self.assertEqual(tlist, ('0',))

        # Fails immediately on the first bad value.
        tlist = self.doit('%cr Funky 3 Medina')
        self.assertEqual(tlist, ('0',))


    def test_pingpong(self):
        # cycle stops before repeating min
        tlist = self.doit('%pingpong 0 4')
        self.assertEqual(tlist, ('0', '1', '2', '3', '4', '3', '2', '1'))

        # %pp is a synonym for pingpong
        tlist = self.doit('%pp 3 -3')
        self.assertEqual(tlist, ('-3', '-2', '-1', '0', '1', '2', '3', '2', '1', '0', '-1', '-2'))

        #step
        tlist = self.doit('%ping 11 23 4')
        self.assertEqual(tlist, ('11', '15', '19', '23', '19', '15'))
        tlist = self.doit('%ping 11 23 -4')
        self.assertEqual(tlist, ('23', '19', '15', '11', '15', '19'))
        tlist = self.doit('%PING -23 -11 4')
        self.assertEqual(tlist, ('-23', '-19', '-15', '-11', '-15', '-19'))

        # uneven step
        tlist = self.doit('%pi 7 21 3')
        self.assertEqual(tlist, ('7', '10', '13', '16', '19', '16', '13', '10'))
        tlist = self.doit('%pi 7 21 -3')
        self.assertEqual(tlist, ('21', '18', '15', '12', '9', '12', '15', '18'))
        tlist = self.doit('%pi -21 -7 3')
        self.assertEqual(tlist, ('-21', '-18', '-15', '-12', '-9', '-12', '-15', '-18'))

        # step is bigger than the total difference between min and max
        tlist = self.doit('%p 5 0 8')
        self.assertEqual(tlist, ('0',))
        tlist = self.doit('%p 5 0 -8')
        self.assertEqual(tlist, ('5',))

        # edges
        tlist = self.doit('%p 3 3 -1')
        self.assertEqual(tlist, ('3',))
        tlist = self.doit('%p -3 -3 1')
        self.assertEqual(tlist, ('-3',))
        tlist = self.doit('%p 3 4 1')
        self.assertEqual(tlist, ('3', '4'))
        tlist = self.doit('%p 4 3 -1')
        self.assertEqual(tlist, ('4', '3'))

        # bad values: same test cases as for %range
        tlist = self.doit('%p Funky Cold Medina')
        self.assertEqual(tlist, ('0',))
        tlist = self.doit('%p Funky 3 Medina')
        self.assertEqual(tlist, ('0',))
        tlist = self.doit('%p 3 3.14 Medina')
        self.assertEqual(tlist, ('0', '1', '2', '3', '2', '1'))
        tlist = self.doit('%p 3 5 3.14')
        self.assertEqual(tlist, ('3', '4', '5', '4'))
        tlist = self.doit('%p 3 5 0')
        self.assertEqual(tlist, ('3', '4', '5', '4'))

    def test_curve(self):
        tlist = self.doit('%CURVE LINEAR IN 5 0 1 2 3 4')
        self.assertEqual(''.join(tlist), '01234')
        tlist = self.doit('%curv lin OUT 6 A B C')
        self.assertEqual(''.join(tlist), 'AABBCC')
        tlist = self.doit('%cu lin INOUT 8 A B C D')
        self.assertEqual(''.join(tlist), 'AABBCCDD')
        tlist = self.doit('%cu lin INOUT 7 A')
        self.assertEqual(''.join(tlist), 'AAAAAAA')

        tlist = self.doit('%cu sine I 11 A B C D')
        self.assertEqual(''.join(tlist), 'AAAABBBCCDD')
        tlist = self.doit('%cu sine O 11 A B C D')
        self.assertEqual(''.join(tlist), 'AABBCCCDDDD')
        tlist = self.doit('%cu sin IO 19 A B C D')
        self.assertEqual(''.join(tlist), 'AAAAABBBBBCCCCDDDDD')

        tlist = self.doit('%cu quadratic i 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAABBBBBCCCDDEE')
        tlist = self.doit('%cu quad o 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AABBCCCDDDDDEEEEEEE')
        tlist = self.doit('%cu quad io 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAABBBCCCDDDEEEEE')

        tlist = self.doit('%cu cubic i 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAAAAABBBCCCDDE')
        tlist = self.doit('%cu cub o 19 A B C D E')
        self.assertEqual(''.join(tlist), 'ABBCCCDDDEEEEEEEEEE')
        tlist = self.doit('%cu cub io 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAABBBCDDDEEEEEE')

        tlist = self.doit('%cu quartic i 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAAAAAABBBBCCDE')
        tlist = self.doit('%cu quart o 19 A B C D E')
        self.assertEqual(''.join(tlist), 'ABCCDDDDEEEEEEEEEEE')
        tlist = self.doit('%cu quar io 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAABBCDDEEEEEEE')

        tlist = self.doit('%cu quintic i 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAAAAAAABBBCCDE')
        tlist = self.doit('%cu quint o 19 A B C D E')
        self.assertEqual(''.join(tlist), 'ABCCDDDEEEEEEEEEEEE')
        tlist = self.doit('%cu qui io 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAABBCDDEEEEEEE')

        tlist = self.doit('%cu exponential i 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAAAAAAAABBBCDE')
        tlist = self.doit('%cu expon o 19 A B C D E')
        self.assertEqual(''.join(tlist), 'ABCDDDEEEEEEEEEEEEE')
        tlist = self.doit('%cu exp io 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAAABCDEEEEEEEE')

        tlist = self.doit('%cu circular i 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAAAABBBBBBCCDE')
        tlist = self.doit('%cu circ o 19 A B C D E')
        self.assertEqual(''.join(tlist), 'ABCCDDDDDDEEEEEEEEE')
        tlist = self.doit('%cu ci io 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAABBBCDDDEEEEEE')

        tlist = self.doit('%cu bounce i 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAABBBBBABCDDEEE')
        tlist = self.doit('%cu bou o 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAABBCDEDDDDDEEEEEE')
        tlist = self.doit('%cu bo io 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAABCCCDEEEEEEE')

        # no function doesn't crash
        tlist = self.doit('%cu')
        self.assertEqual(''.join(tlist), '')
        # bad function falls back to LINEAR
        tlist = self.doit('%cu afafawef io 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAABBBBCCCCCDDDDEEE')
        # bad direction falls back to IN
        tlist = self.doit('%cu expo adfae 19 A B C D E')
        self.assertEqual(''.join(tlist), 'AAAAAAAAAAAAABBBCDE')
        # bad period falls back to 2
        tlist = self.doit('%cu expo in adffae A B C D E')
        self.assertEqual(''.join(tlist), 'AE')
        # period less than 2 gets set to 2 (to avoid negative periods or divide by zero funk)
        tlist = self.doit('%cu expo in -19 A B C D E')
        self.assertEqual(''.join(tlist), 'AE')
        tlist = self.doit('%cu expo in 0 A B C D E')
        self.assertEqual(''.join(tlist), 'AE')
        tlist = self.doit('%cu expo in 1 A B C D E')
        self.assertEqual(''.join(tlist), 'AE')
        # no values, no love
        tlist = self.doit('%cu expo in 19')
        self.assertEqual(''.join(tlist), '')

    def test_autocomplete_curve(self):
        self.assertEqual(expanders.autocomplete_curve_function('qu'), 'QUADRATIC')
        self.assertEqual(expanders.autocomplete_curve_function('qua'), 'QUADRATIC')
        self.assertEqual(expanders.autocomplete_curve_function('quar'), 'QUARTIC')
        self.assertEqual(expanders.autocomplete_curve_function(''), 'LINEAR')

    def test_asterisk(self):
        tlist = self.doit('A -B.B+*4 C')
        self.assertEqual(''.join(tlist), 'A-B.B+-B.B+-B.B+-B.B+C')
        # no left side -- should be excluded
        tlist = self.doit('*4 C *')
        self.assertEqual(''.join(tlist), 'C')
        # no right side -- treat as 1
        tlist = self.doit('A B -C+*')
        self.assertEqual(''.join(tlist), 'AB-C+')
        # invalid multiplier -- treat as 1
        tlist = self.doit('A B C*q D*3.14')
        self.assertEqual(''.join(tlist), 'ABCD')
        # multiply by 0
        tlist = self.doit('A B*0 C D')
        self.assertEqual(''.join(tlist), 'ACD')


