import unittest
import math

import calculator.core.parser as parser
from calculator.core.exception import EvaluationException
from calculator.core.evaluator import *


class EvaluatorTest(unittest.TestCase):
    def setUp(self):
        functions = {
            'abs': lambda a: a if a >= 0 else -a,
            'cos': math.cos,
            'mult': lambda a, m=2: a * m
        }

        context = EvaluatorContext(constants=None, functions=functions)
        self._evaluator = Evaluator(context)

    def test_basic_evaluation(self):
        v1 = self._evaluator.evaluate('1 + 2 - 5')
        self.assertEqual(v1, 1 + 2 - 5)

        v2 = self._evaluator.evaluate('1 ÷ 2 × 4')
        self.assertEqual(v2, 1 / 2 * 4)

        v3 = self._evaluator.evaluate('1 + 2 × 3')
        self.assertEqual(v3, 1 + 2 * 3)

        v4 = self._evaluator.evaluate('(10 - 15) × 2')
        self.assertEqual(v4, (10 - 15) * 2)

        v5 = self._evaluator.evaluate('5.5 ÷ -7')
        self.assertEqual(v5, 5.5 / -7)

        v6 = self._evaluator.evaluate('1 + 4^2')
        self.assertEqual(v6, 17)

        v7 = self._evaluator.evaluate('4! - 10')
        self.assertEqual(v7, 14)

        v8 = self._evaluator.evaluate('1 + -4!')
        self.assertEqual(v8, -23)

    def test_func_call_evaluation(self):
        v1 = self._evaluator.evaluate('abs(2-5)')
        self.assertEqual(v1, 3)

        v2 = self._evaluator.evaluate('cos(2 × π)')
        self.assertEqual(v2, 1.0)

        v3 = self._evaluator.evaluate('abs (cos(π) )')
        self.assertEqual(v3, 1.0)

        v4 = self._evaluator.evaluate('1 - abs(-3) × 2')
        self.assertEqual(v4, -5)

    def test_invalid_evaluation(self):
        with self.assertRaises(EvaluationException) as cm:
            self._evaluator.evaluate('1 + a - 2')

        self.assertIn('unknown constant', cm.exception.args[0])

        with self.assertRaises(EvaluationException) as cm:
            self._evaluator.evaluate('1 + foo(10) × 2')

        self.assertIn('unsupported function', cm.exception.args[0])

        with self.assertRaises(EvaluationException) as cm:
            self._evaluator.evaluate('abs(1, -2)')

        self.assertIn('incorrect number of arguments', cm.exception.args[0])

        try:
            v1 = self._evaluator.evaluate('mult(10)')
            self.assertEqual(v1, 20)
        except EvaluationException:
            self.fail("EvaluationException shall not be raised")

        try:
            v2 = self._evaluator.evaluate('mult(10, 3)')
            self.assertEqual(v2, 30)
        except EvaluationException:
            self.fail("EvaluationException shall not be raised")

        with self.assertRaises(EvaluationException) as cm:
            self._evaluator.evaluate('mult()')

        self.assertIn('incorrect number of arguments', cm.exception.args[0])

        with self.assertRaises(EvaluationException) as cm:
            self._evaluator.evaluate('mult(1, 2, 3)')

        self.assertIn('incorrect number of arguments', cm.exception.args[0])

    def test_invalid_special_case(self):
        with self.assertRaises(EvaluationException):
            self._evaluator.evaluate('1 ÷ 0')

        with self.assertRaises(EvaluationException):
            self._evaluator.evaluate('(-1) ^ 0.5')
