import inspect
from typing import List, Tuple, Sequence

import calculator.core.tokens as tokens
import calculator.core.nodes as nodes
from calculator.core.constants import BinaryOperators, UnaryOperators, OperatorAffix, Separators, MATH_CONSTANTS
from calculator.core.structs import OperatorInfo
from calculator.core.exception import ParsingException


NAME_CHAR_SPECIALS = frozenset(['π', '_'])
VALID_SEPARATORS = frozenset([Separators.SEP_COMMA])

BINOP_TABLE = {
    BinaryOperators.OP_ADD: OperatorInfo(BinaryOperators.OP_ADD, 5),
    BinaryOperators.OP_MINUS: OperatorInfo(BinaryOperators.OP_MINUS, 5),
    BinaryOperators.OP_MULTIPLY: OperatorInfo(BinaryOperators.OP_MULTIPLY, 6),
    BinaryOperators.OP_DIVIDE: OperatorInfo(BinaryOperators.OP_DIVIDE, 6),
    BinaryOperators.OP_MOD: OperatorInfo(BinaryOperators.OP_MOD, 6),
    BinaryOperators.OP_POWER: OperatorInfo(BinaryOperators.OP_POWER, 7)
}

UNARYOP_TABLE = {
    UnaryOperators.OP_NEGATIVE: OperatorInfo(UnaryOperators.OP_NEGATIVE, 5, OperatorAffix.PREFIX),
    UnaryOperators.OP_POSITIVE: OperatorInfo(UnaryOperators.OP_POSITIVE, 5, OperatorAffix.PREFIX),
    UnaryOperators.OP_FACTORIAL: OperatorInfo(UnaryOperators.OP_FACTORIAL, 6, OperatorAffix.POSTFIX)
}


def tokenize(exp: str) -> List[tokens.Token]:
    """
    convert the given string expression into a list of tokens
    """

    def is_name_char(char: str) -> bool:
        # only check after number token, safe to use isnumeric
        return char.isalpha() or char.isnumeric() or (char in NAME_CHAR_SPECIALS)

    def is_op(char: str) -> bool:
        return (char in BINOP_TABLE) or (char in UNARYOP_TABLE)

    def read_number(start: int, token_list: list) -> int:
        state_map = {
            'start': ['int', 'fraction'],
            'int': ['fraction', 'exponent', 'end'],
            'fraction': ['exponent', 'end'],
            'exponent': ['exponent_value'],
            'exponent_value': ['end']
        }

        state = 'start'

        is_end = False
        i = start
        while not is_end and i < len(exp):
            char = exp[i]
            if char.isnumeric():
                if state == 'start':
                    state = 'int'
                elif state == 'exponent':
                    state = 'exponent_value'

                i += 1
            elif char == Separators.SEP_DOT:
                if 'fraction' in state_map[state]:
                    state = 'fraction'
                    i += 1
                else:
                    raise ParsingException("invalid '.'", i)
            elif char.isalpha():
                if char == 'e' or char == 'E':
                    if 'exponent' in state_map[state]:
                        state = 'exponent'
                        i += 1
                    else:
                        raise ParsingException("invalid 'e'", i)
                else:
                    raise ParsingException(f"invalid character '{char}'", i)
            elif char == UnaryOperators.OP_NEGATIVE or char == UnaryOperators.OP_POSITIVE:
                if 'exponent_value' in state_map[state]:
                    state = 'exponent_value'
                    i += 1
                else:
                    is_end = True
            else:
                is_end = True

        if 'end' in state_map[state]:
            content = exp[start : i]
            if state == 'int':
                num = int(content)
            else:
                num = float(content)
            token_list.append(tokens.TokenNumber(num, pos=start))

            return i
        else:
            if is_end:
                raise ParsingException(f"invalid character '{exp[i - 1]}'", i - 1)
            else:
                raise ParsingException(f"invalid character '{exp[i]}'", i)

    def read_name(start: int, token_list: list) -> int:
        i = start
        while i < len(exp) and is_name_char(exp[i]):
            i += 1

        token = tokens.TokenName(exp[start : i], pos=start)
        token_list.append(token)

        return i

    if not isinstance(exp, str):
        raise TypeError("invalid exp")

    if exp == '':
        raise ValueError("exp is empty")

    token_list: List[tokens.Token] = []

    i = 0
    while i < len(exp):
        char = exp[i]

        if is_op(char) or char in VALID_SEPARATORS:
            token_list.append(tokens.TokenSymbol(char, pos=i))
            i += 1
        elif char == Separators.SEP_LEFT_BRACKET:
            token_list.append(tokens.TokenOpenBracket(pos=i))
            i += 1
        elif char == Separators.SEP_RIGHT_BRACKET:
            token_list.append(tokens.TokenCloseBracket(pos=i))
            i += 1
        elif char == Separators.SEP_DOT or char.isnumeric():
            i = read_number(i, token_list)
        elif char == ' ':
            i += 1
        elif is_name_char(char):
            i = read_name(i, token_list)
        else:
            raise ParsingException(f"invalid character '{char}'", i)

    return token_list

def build_expression_tree(token_list: Sequence[tokens.Token]) -> nodes.ExpNode:
    """
    convert a list of tokens into expression tree
    """

    def is_unary_op(op) -> bool:
        return op in UNARYOP_TABLE

    def is_open_bracket(token) -> bool:
        return isinstance(token, tokens.TokenOpenBracket)

    def is_close_bracket(token) -> bool:
        return isinstance(token, tokens.TokenCloseBracket)

    def is_comma(token) -> bool:
        return isinstance(token, tokens.TokenSymbol) and token.symbol == Separators.SEP_COMMA

    def is_higher_or_equal_op_priority(op1, op2, table) -> bool:
        oi1 = table.get(op1)
        oi2 = table.get(op2)

        p1 = 0 if oi1 is None else oi1.priority
        p2 = 0 if oi2 is None else oi2.priority

        return p1 >= p2

    def read_exp_chain(index) -> Tuple[nodes.ExpNode, int]:
        token = token_list[index]
        if isinstance(token, tokens.TokenSymbol):
            if is_open_bracket(token):
                node, i = read_exp(index)
            elif is_unary_op(token.symbol):
                if UNARYOP_TABLE[token.symbol].affix == OperatorAffix.PREFIX:
                    node, i = read_prefix_unary_exp(index)
                else:
                    raise ParsingException(f"unary operator '{token.symbol}' is not a prefix operator", token.pos)
            else:
                raise ParsingException(f"unexpected symbol '{token.symbol}'", token.pos)
        else:
            node, i = read_exp(index)

        if i < len(token_list):
            # look ahead for 1 token
            next_token = token_list[i]
            if isinstance(next_token, tokens.TokenSymbol) and is_unary_op(next_token.symbol):
                if UNARYOP_TABLE[next_token.symbol].affix == OperatorAffix.POSTFIX:
                    node, i = read_postfix_unary_exp(i, node)
        else:
            return (node, i)

        if i < len(token_list):
            # look ahead for 1 token
            next_token = token_list[i]
            if is_close_bracket(next_token):
                return (node, i)
            elif isinstance(next_token, tokens.TokenSymbol):
                if next_token.symbol == Separators.SEP_COMMA:
                    return (node, i)
                elif next_token.symbol in BINOP_TABLE:
                    return read_binary_exp(i, node)
                else:
                    raise ParsingException(f"unexpected symbol '{next_token.symbol}'", next_token.pos)
            else:
                raise ParsingException("unexpected token", next_token.pos)
        else:
            return (node, i)

    def read_exp(index) -> Tuple[nodes.ExpNode, int]:
        if index >= len(token_list):
            raise ParsingException("unexpected token", token_list[-1].pos)

        token = token_list[index]
        if is_open_bracket(token):
            return read_bracket_exp(index)
        elif isinstance(token, tokens.TokenNumber):
            return (nodes.NumberNode(token.num, pos=token.pos), index + 1)
        elif isinstance(token, tokens.TokenName):
            if (index + 1) < len(token_list) and is_open_bracket(token_list[index + 1]):
                return read_func_call(index)
            else:
                return (nodes.NameConstantNode(token.name, pos=token.pos), index + 1)
        elif isinstance(token, tokens.TokenSymbol):
            raise ParsingException(f"unexpected symbol '{token.symbol}'", token.pos)
        else:
            raise ParsingException("unexpceted token", token.pos)

    def read_bracket_exp(index) -> Tuple[nodes.ExpNode, int]:
        node, i = read_exp_chain(index + 1)

        if i < len(token_list) and is_close_bracket(token_list[i]):
            return (node, i + 1)
        else:
            raise ParsingException("unmatch '('", token_list[index].pos)

    def read_prefix_unary_exp(index) -> Tuple[nodes.UnaryOpNode, int]:
        node, i = read_exp(index + 1)
        token = token_list[index]
        return (nodes.UnaryOpNode(token.symbol, node, pos=token.pos), i)

    def read_postfix_unary_exp(index, child: nodes.ExpNode) -> Tuple[nodes.UnaryOpNode, int]:
        token = token_list[index]

        if isinstance(child, nodes.UnaryOpNode):
            if is_higher_or_equal_op_priority(token.symbol, child.op, UNARYOP_TABLE):
                node = nodes.UnaryOpNode(token.symbol, child.child, pos=token.pos)
                child.child = node
                node = child
            else:
                node = nodes.UnaryOpNode(token.symbol, child, pos=token.pos)
        else:
            node = nodes.UnaryOpNode(token.symbol, child, pos=token.pos)

        return (node, index + 1)

    def read_binary_exp(index, left: nodes.ExpNode) -> Tuple[nodes.BinaryOpNode, int]:
        right, i = read_exp_chain(index + 1)

        token = token_list[index]
        if isinstance(right, nodes.BinaryOpNode) and not is_open_bracket(token_list[index + 1]):
            # check operator priority and rotate the expression tree when necessary.
            # when priority of two operators are equal, we also should rotate the tree
            # in case these operators don't follow the commutative law.
            if is_higher_or_equal_op_priority(token.symbol, right.op, BINOP_TABLE):
                node = nodes.BinaryOpNode(token.symbol, left, right.left, pos=token.pos)
                right.left = node
                node = right
            else:
                node = nodes.BinaryOpNode(token.symbol, left, right, pos=token.pos)
        else:
            node = nodes.BinaryOpNode(token.symbol, left, right, pos=token.pos)

        return (node, i)

    def read_func_call(index) -> Tuple[nodes.FuncCallNode, int]:
        name_token = token_list[index]
        index += 2  # skip '('

        token_count = len(token_list)

        node = None
        i = index
        args = []

        while i < token_count and not is_close_bracket(token_list[i]):
            node, i = read_exp_chain(i)
            args.append(node)
            if i < token_count and is_comma(token_list[i]):
                i += 1
            else:
                break

        if i < token_count and is_close_bracket(token_list[i]):
            func_node = nodes.FuncCallNode(name_token.name, args, pos=name_token.pos)
            return (func_node, i + 1)
        else:
            raise ParsingException("unclose func call", name_token.pos)


    node, i = read_exp_chain(0)

    if i < len(token_list):
        last_token = token_list[i]
        if is_close_bracket(last_token):
            raise ParsingException("unmatch ')'", last_token.pos)
        else:
            raise ParsingException("unexpected token", last_token.pos)
    else:
        return node

def parse_expression(expression: str) -> nodes.ExpNode:
    """
    parse the given string expression into an expression tree
    """

    tokens = tokenize(expression)
    node = build_expression_tree(tokens)

    return node
