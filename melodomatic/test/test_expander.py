import unittest
import testhelper
import consts, expanders

class ExpanderTest(unittest.TestCase):
    def setUp(self):
        testhelper.setUp()
    def tearDown(self):
        testhelper.tearDown()
    def doit(self, s):
        a = testhelper.tokenize(s)
        return expanders.expand_list(a)

    def test_bare(self):
        list = self.doit('FOO')
        self.assertEqual(list, ('FOO',))
        list = self.doit('$guh 2 Q a28 !#7@ 6 7 8')
        self.assertEqual(list, ('$guh','2','Q','a28','!#7@','6','7','8'))

    def test_simple_parentheses(self):
        list = self.doit('A (B C D) (E F (G)) (H (I J) (K L) M) N')
        self.assertEqual(list, ('A','B','C','D','E','F','G','H','I','J','K','L','M','N'))
        list = self.doit('()')
        self.assertEqual(list, ())

        # unclosed parentheis: don't care
        list = self.doit('A (B C D) (E F (G)')
        self.assertEqual(list, ('A','B','C','D','E','F','G'))

        # stray close: drop everything after the last close
        list = self.doit('A (B C D) E) F')
        self.assertEqual(list, ('A','B','C','D', 'E'))

    def test_list(self):
        list = self.doit('%list A (B C D) (%li E F (G)) (%l H (%list I J) (K L) M) N')
        self.assertEqual(list, ('A','B','C','D','E','F','G','H','I','J','K','L','M','N'))
        list = self.doit('%list')
        self.assertEqual(list, ())

    def test_xerox(self):
        list = self.doit('%xerox 3 QRS')
        self.assertEqual(list, ('QRS', 'QRS', 'QRS'))
        list = self.doit('%x 3 X Y Z')
        self.assertEqual(list, ('X', 'Y', 'Z', 'X', 'Y', 'Z', 'X', 'Y', 'Z'))

        # oops, swapped count and value
        list = self.doit('%xErOx QRS 3')
        self.assertEqual(list, ('3',))

        # Bad command gets replaced with LIST
        list = self.doit('%xeroxA B C D')
        self.assertEqual(list, ('B','C','D'))

    def test_range(self):
        # %range is inclusive of min and max
        list = self.doit('%range 0 4')
        self.assertEqual(list, ('0', '1', '2', '3', '4'))

        # min and max are reversed
        list = self.doit('%Ran 3 -3')
        self.assertEqual(list, ('-3', '-2', '-1', '0', '1', '2', '3'))

        # step
        list = self.doit('%ra 11 19 4')
        self.assertEqual(list, ('11', '15', '19'))

        # negative step
        list = self.doit('%r 4 2 -1')
        self.assertEqual(list, ('4', '3', '2'))

        # edges
        list = self.doit('%r 3 3 -1')
        self.assertEqual(list, ('3',))
        list = self.doit('%r -3 -3 1')
        self.assertEqual(list, ('-3',))
        list = self.doit('%r 3 4 1')
        self.assertEqual(list, ('3', '4'))
        list = self.doit('%r 4 3 -1')
        self.assertEqual(list, ('4', '3'))

        # swapped + negative step + uneven ending:
        # first step is guaranteed to be min/max
        # last value is not guaranteed to be min/max if the step is uneven
        list = self.doit('%r 7 21 -3')
        self.assertEqual(list, ('21', '18', '15', '12', '9'))

        # bad values
        # min and max default to 0.
        list = self.doit('%r Funky Cold Medina')
        self.assertEqual(list, ('0',))

        # Fails immediately on the first bad value.
        list = self.doit('%r Funky 3 Medina')
        self.assertEqual(list, ('0',))

        # If min is set and it fails on max, swapping kicks in and we get 0-3.
        # No floats
        list = self.doit('%r 3 3.14159 Medina')
        self.assertEqual(list, ('0', '1', '2', '3',))

        # step defaults to 1.
        list = self.doit('%r 3 5 3.14')
        self.assertEqual(list, ('3','4','5'))

        # step cannot be 0, will get turned into 1
        list = self.doit('%r 3 5 0')
        self.assertEqual(list, ('3','4','5'))

    def test_crange(self):
        list = self.doit('%crange 2 4 1')
        self.assertEqual(list, ('0', '1', '2', '3', '4'))

        # step, odd range
        list = self.doit('%crange 12 9 3')
        self.assertEqual(list, ('9', '12', '15',))

        # negative step
        list = self.doit('%crange 2 4 -1')
        self.assertEqual(list, ('4', '3', '2', '1', '0'))

        # negative spread
        list = self.doit('%crange 23 -8 2')
        self.assertEqual(list, ('19', '21', '23', '25', '27'))
        list = self.doit('%crange 23 -8 -2')
        self.assertEqual(list, ('27', '25', '23', '21', '19'))

        # 0 range
        list = self.doit('%cr 12 0 3')
        self.assertEqual(list, ('12',))

        # 0 step
        list = self.doit('%cr 12 4 0')
        self.assertEqual(list, ('10', '11', '12', '13', '14'))

        # bad values
        list = self.doit('%cr Funky Cold Medina')
        self.assertEqual(list, ('0',))

        # Fails immediately on the first bad value.
        list = self.doit('%cr Funky 3 Medina')
        self.assertEqual(list, ('0',))


    def test_pingpong(self):
        # cycle stops before repeating min
        list = self.doit('%pingpong 0 4')
        self.assertEqual(list, ('0', '1', '2', '3', '4', '3', '2', '1'))

        # %pp is a synonym for pingpong
        list = self.doit('%pp 3 -3')
        self.assertEqual(list, ('-3', '-2', '-1', '0', '1', '2', '3', '2', '1', '0', '-1', '-2'))

        #step
        list = self.doit('%ping 11 23 4')
        self.assertEqual(list, ('11', '15', '19', '23', '19', '15'))
        list = self.doit('%ping 11 23 -4')
        self.assertEqual(list, ('23', '19', '15', '11', '15', '19'))
        list = self.doit('%PING -23 -11 4')
        self.assertEqual(list, ('-23', '-19', '-15', '-11', '-15', '-19'))

        # uneven step
        list = self.doit('%pi 7 21 3')
        self.assertEqual(list, ('7', '10', '13', '16', '19', '16', '13', '10'))
        list = self.doit('%pi 7 21 -3')
        self.assertEqual(list, ('21', '18', '15', '12', '9', '12', '15', '18'))
        list = self.doit('%pi -21 -7 3')
        self.assertEqual(list, ('-21', '-18', '-15', '-12', '-9', '-12', '-15', '-18'))

        # step is bigger than the total difference between min and max
        list = self.doit('%p 5 0 8')
        self.assertEqual(list, ('0',))
        list = self.doit('%p 5 0 -8')
        self.assertEqual(list, ('5',))

        # edges
        list = self.doit('%p 3 3 -1')
        self.assertEqual(list, ('3',))
        list = self.doit('%p -3 -3 1')
        self.assertEqual(list, ('-3',))
        list = self.doit('%p 3 4 1')
        self.assertEqual(list, ('3', '4'))
        list = self.doit('%p 4 3 -1')
        self.assertEqual(list, ('4', '3'))

        # bad values: same test cases as for %range
        list = self.doit('%p Funky Cold Medina')
        self.assertEqual(list, ('0',))
        list = self.doit('%p Funky 3 Medina')
        self.assertEqual(list, ('0',))
        list = self.doit('%p 3 3.14 Medina')
        self.assertEqual(list, ('0', '1', '2', '3', '2', '1'))
        list = self.doit('%p 3 5 3.14')
        self.assertEqual(list, ('3', '4', '5', '4'))
        list = self.doit('%p 3 5 0')
        self.assertEqual(list, ('3', '4', '5', '4'))

    def test_curve(self):
        list = self.doit('%CURVE LINEAR IN 5 0 1 2 3 4')
        self.assertEqual(''.join(list), '01234')
        list = self.doit('%curv lin OUT 6 A B C')
        self.assertEqual(''.join(list), 'AABBCC')
        list = self.doit('%cu lin INOUT 7 A B C D')
        self.assertEqual(''.join(list), 'ABBCCDD')
        list = self.doit('%cu lin INOUT 7 A')
        self.assertEqual(''.join(list), 'AAAAAAA')

        list = self.doit('%cu sine I 11 A B C D')
        self.assertEqual(''.join(list), 'AAAABBBCCDD')
        list = self.doit('%cu sine O 11 A B C D')
        self.assertEqual(''.join(list), 'AABBCCCDDDD')
        list = self.doit('%cu sin IO 19 A B C D')
        self.assertEqual(''.join(list), 'AAAAABBBBBCCCCDDDDD')

        list = self.doit('%cu quadratic i 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAABBBBBCCCDDEE')
        list = self.doit('%cu quad o 19 A B C D E')
        self.assertEqual(''.join(list), 'AABBCCCDDDDDEEEEEEE')
        list = self.doit('%cu quad io 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAABBBCCCDDDEEEEE')

        list = self.doit('%cu cubic i 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAAAABBBBCCCDDE')
        list = self.doit('%cu cub o 19 A B C D E')
        self.assertEqual(''.join(list), 'ABBCCCDDDEEEEEEEEEE')
        list = self.doit('%cu cub io 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAABBBCDDDEEEEEE')

        list = self.doit('%cu quartic i 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAAAAAABBBBCCDE')
        list = self.doit('%cu quart o 19 A B C D E')
        self.assertEqual(''.join(list), 'ABCCDDDDEEEEEEEEEEE')
        list = self.doit('%cu quar io 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAABBCDDEEEEEEE')

        list = self.doit('%cu quintic i 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAAAAAAABBBCCDE')
        list = self.doit('%cu quint o 19 A B C D E')
        self.assertEqual(''.join(list), 'ABCCDDDEEEEEEEEEEEE')
        list = self.doit('%cu qui io 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAABBCDDEEEEEEE')

        list = self.doit('%cu exponential i 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAAAAAAAABBBCDE')
        list = self.doit('%cu expon o 19 A B C D E')
        self.assertEqual(''.join(list), 'ABCDDDEEEEEEEEEEEEE')
        list = self.doit('%cu exp io 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAAABCDEEEEEEEE')

        list = self.doit('%cu circular i 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAAAABBBBBBCCDE')
        list = self.doit('%cu circ o 19 A B C D E')
        self.assertEqual(''.join(list), 'ABCCDDDDDDEEEEEEEEE')
        list = self.doit('%cu ci io 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAABBBCDDDEEEEEE')

        list = self.doit('%cu bounce i 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAABBBBBABCDDEEE')
        list = self.doit('%cu bou o 19 A B C D E')
        self.assertEqual(''.join(list), 'AAABBCDEDDDDDEEEEEE')
        list = self.doit('%cu bo io 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAABCCCDEEEEEEE')

        # no function doesn't crash
        list = self.doit('%cu')
        self.assertEqual(''.join(list), '')
        # bad function falls back to LINEAR
        list = self.doit('%cu afafawef io 19 A B C D E')
        self.assertEqual(''.join(list), 'AAABBBBCCCCCDDDDEEE')
        # bad direction falls back to IN
        list = self.doit('%cu expo adfae 19 A B C D E')
        self.assertEqual(''.join(list), 'AAAAAAAAAAAAABBBCDE')
        # bad period falls back to 2
        list = self.doit('%cu expo in adffae A B C D E')
        self.assertEqual(''.join(list), 'AE')
        # period less than 2 gets set to 2 (to avoid negative periods or divide by zero funk)
        list = self.doit('%cu expo in -19 A B C D E')
        self.assertEqual(''.join(list), 'AE')
        list = self.doit('%cu expo in 0 A B C D E')
        self.assertEqual(''.join(list), 'AE')
        list = self.doit('%cu expo in 1 A B C D E')
        self.assertEqual(''.join(list), 'AE')
        # no values, no love
        list = self.doit('%cu expo in 19')
        self.assertEqual(''.join(list), '')

    def test_autocomplete_curve(self):
        self.assertEqual(expanders.autocomplete_curve_function('qu'), 'QUADRATIC')
        self.assertEqual(expanders.autocomplete_curve_function('qua'), 'QUADRATIC')
        self.assertEqual(expanders.autocomplete_curve_function('quar'), 'QUARTIC')
        self.assertEqual(expanders.autocomplete_curve_function(''), 'LINEAR')

    def test_asterisk(self):
        list = self.doit('A -B.B+*4 C')
        self.assertEqual(''.join(list), 'A-B.B+-B.B+-B.B+-B.B+C')
        # no left side -- should be excluded
        list = self.doit('*4 C *')
        self.assertEqual(''.join(list), 'C')
        # no right side -- treat as 1
        list = self.doit('A B -C+*')
        self.assertEqual(''.join(list), 'AB-C+')
        # invalid multiplier -- treat as 1
        list = self.doit('A B C*q D*3.14')
        self.assertEqual(''.join(list), 'ABCD')
        # multiply by 0
        list = self.doit('A B*0 C D')
        self.assertEqual(''.join(list), 'ACD')


