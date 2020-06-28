import unittest

import calculator.core.parser as parser
from calculator.core.tokens import *
from calculator.core.exception import ParsingException

class TokenizingTest(unittest.TestCase):
    def test_basic_exp_parsing(self):
        tokens = parser.tokenize('100 + 200')
        self.assertEqual(len(tokens), 3)
        self.assertIsInstance(tokens[0], TokenNumber)
        self.assertEqual(tokens[0].num, 100)
        self.assertEqual(tokens[0].pos, 0)
        self.assertIsInstance(tokens[1], TokenSymbol)
        self.assertEqual(tokens[1].symbol, '+')
        self.assertEqual(tokens[1].pos, 4)
        self.assertIsInstance(tokens[2], TokenNumber)
        self.assertEqual(tokens[2].num, 200)
        self.assertEqual(tokens[2].pos, 6)

        tokens = parser.tokenize('1+2 × 2.2 - 10')
        self.assertEqual(len(tokens), 7)
        self.assertIsInstance(tokens[0], TokenNumber)
        self.assertEqual(tokens[0].num, 1)
        self.assertEqual(tokens[0].pos, 0)
        self.assertIsInstance(tokens[1], TokenSymbol)
        self.assertEqual(tokens[1].symbol, '+')
        self.assertEqual(tokens[1].pos, 1)
        self.assertIsInstance(tokens[2], TokenNumber)
        self.assertEqual(tokens[2].num, 2)
        self.assertEqual(tokens[2].pos, 2)
        self.assertIsInstance(tokens[3], TokenSymbol)
        self.assertEqual(tokens[3].symbol, '×')
        self.assertEqual(tokens[3].pos, 4)
        self.assertIsInstance(tokens[4], TokenNumber)
        self.assertEqual(tokens[4].num, 2.2)
        self.assertEqual(tokens[4].pos, 6)
        self.assertIsInstance(tokens[5], TokenSymbol)
        self.assertEqual(tokens[5].symbol, '-')
        self.assertEqual(tokens[5].pos, 10)
        self.assertIsInstance(tokens[6], TokenNumber)
        self.assertEqual(tokens[6].num, 10)
        self.assertEqual(tokens[6].pos, 12)

    def test_exp_with_bracket(self):
        tokens = parser.tokenize('100 × (200 + 10)')
        self.assertEqual(len(tokens), 7)
        self.assertIsInstance(tokens[2], TokenOpenBracket)
        self.assertEqual(tokens[2].pos, 6)
        self.assertIsInstance(tokens[6], TokenCloseBracket)
        self.assertEqual(tokens[6].pos, 15)

    def test_number_tokenizing(self):
        tokens = parser.tokenize('1 + 100')
        self.assertIsInstance(tokens[2].num, int)
        self.assertEqual(tokens[2].num, 100)

        tokens = parser.tokenize('1 + 100.3')
        self.assertEqual(tokens[2].num, 100.3)

        tokens = parser.tokenize('1 + 100.')
        self.assertIsInstance(tokens[2].num, float)
        self.assertEqual(tokens[2].num, 100.0)

        tokens = parser.tokenize('1 + .2')
        self.assertIsInstance(tokens[2].num, float)
        self.assertEqual(tokens[2].num, 0.2)

        tokens = parser.tokenize('1 + 3e10')
        self.assertEqual(tokens[2].num, 3e10)

        tokens = parser.tokenize('1 + 3.1e-5')
        self.assertEqual(tokens[2].num, 3.1e-5)

    def test_name_tokenizing(self):
        tokens = parser.tokenize('1 + π × 30')
        self.assertEqual(len(tokens), 5)
        self.assertIsInstance(tokens[2], TokenName)
        self.assertEqual(tokens[2].name, 'π')

        tokens = parser.tokenize('1 + sin(2 × π)')
        self.assertEqual(len(tokens), 8)

    def test_special_name_tokenizing(self):
        tokens = parser.tokenize('1 + a_0 - 1')
        self.assertEqual(len(tokens), 5)
        self.assertIsInstance(tokens[2], TokenName)
        self.assertEqual(tokens[2].name, 'a_0')

        with self.assertRaises(ParsingException) as cm:
            parser.tokenize('1 + 0a - 1')

        self.assertIn('a', cm.exception.args[0])
        self.assertEqual(cm.exception.pos, 6)
