import math

class BinaryOperators(object):
    OP_ADD = '+'
    OP_MINUS = '-'
    OP_MULTIPLY = '×'
    OP_DIVIDE = '÷'
    OP_POWER = '^'
    OP_MOD = '%'

class UnaryOperators(object):
    OP_NEGATIVE = '-'
    OP_POSITIVE = '+'
    OP_FACTORIAL = '!'

class OperatorAffix(object):
    INFIX = 1
    PREFIX = 2
    POSTFIX = 3

class Separators(object):
    SEP_COMMA = ','
    SEP_LEFT_BRACKET = '('
    SEP_RIGHT_BRACKET = ')'
    SEP_DOT = '.'

MATH_CONSTANTS = {
    'π': math.pi,
    'e': math.e
}
