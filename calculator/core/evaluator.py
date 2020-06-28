import math
import inspect
import typing
from typing import Dict, Callable, Union

import calculator.core.parser as parser
import calculator.core.nodes as nodes
from calculator.core.constants import MATH_CONSTANTS, BinaryOperators, UnaryOperators
from calculator.core.exception import EvaluationException


__all__ = ['EvaluatorContext', 'Evaluator']


TypeEvalResult = Union[int, float]


OP_FUNCTIONS_BINARY = {
    BinaryOperators.OP_ADD: lambda a, b: a + b,
    BinaryOperators.OP_MINUS: lambda a, b: a - b,
    BinaryOperators.OP_MULTIPLY: lambda a, b: a * b,
    BinaryOperators.OP_DIVIDE: lambda a, b: a / b,
    BinaryOperators.OP_POWER: lambda a, b: a ** b,
    BinaryOperators.OP_MOD: lambda a, b: a % b
}

OP_FUNCTIONS_UNARY = {
    UnaryOperators.OP_POSITIVE: lambda a: a,
    UnaryOperators.OP_NEGATIVE: lambda a: -a,
    UnaryOperators.OP_FACTORIAL: math.factorial
}


class EvaluatorContext(object):
    """
    context for expression evaluation
    """

    def __init__(self, *, constants: Dict[str, TypeEvalResult] = None, functions: Dict[str, Callable[..., typing.Any]] = None):
        """
        :param constants: add custom constants into context
        :param functions: add custom function into context
        """

        self.constants = dict(MATH_CONSTANTS)
        self.functions = {}

        if constants is not None:
            self.constants.update(constants)

        if functions is not None:
            self.functions.update(functions)

class Evaluator(object):
    """
    the evaluator that can take either string expression or expression tree and output their value
    """

    def __init__(self, context: EvaluatorContext = None):
        if context is not None:
            self._context = context
        else:
            self._context = EvaluatorContext()

        self._eval_methods = (
            (nodes.NumberNode, self._eval_number),
            (nodes.NameConstantNode, self._eval_const),
            (nodes.BinaryOpNode, self._eval_binary),
            (nodes.UnaryOpNode, self._eval_unary),
            (nodes.FuncCallNode, self._eval_func_call)
        )

    def _eval_number(self, node: nodes.NumberNode) -> TypeEvalResult:
        return node.num

    def _eval_const(self, node: nodes.NameConstantNode) -> TypeEvalResult:
        if node.name in self._context.constants:
            return self._context.constants[node.name]
        else:
            raise EvaluationException(f"unknown constant '{node.name}'")

    def _eval_unary(self, node: nodes.UnaryOpNode) -> TypeEvalResult:
        fun = OP_FUNCTIONS_UNARY.get(node.op, None)
        if fun is not None:
            value = self._eval_node(node.child)
            return fun(value)
        else:
            raise EvaluationException(f"unsupported unary operator '{node.op}'")

    def _eval_binary(self, node: nodes.BinaryOpNode) -> TypeEvalResult:
        fun = OP_FUNCTIONS_BINARY.get(node.op, None)
        if fun is not None:
            v_left = self._eval_node(node.left)
            v_right = self._eval_node(node.right)

            result = fun(v_left, v_right)
            if isinstance(result, complex):
                raise EvaluationException("invalid expression")
            else:
                return result
        else:
            raise EvaluationException(f"unsupported binary operator '{node.op}'")

    def _eval_func_call(self, node: nodes.FuncCallNode) -> TypeEvalResult:
        fun = self._context.functions.get(node.id, None)
        if fun is not None:
            # spec validation
            spec = inspect.getfullargspec(fun)
            max_argc = len(spec.args)
            min_argc = max_argc - (0 if spec.defaults is None else len(spec.defaults))
            if min_argc <= len(node.args) <= max_argc:
                values = [self._eval_node(n) for n in node.args]        # resolve arguments
                return fun(*values)
            else:
                raise EvaluationException(f"incorrect number of arguments passed into function '{node.id}'")
        else:
            raise EvaluationException(f"unsupported function '{node.id}'")

    def _eval_node(self, node: nodes.ExpNode) -> TypeEvalResult:
        for (ntype, evaluator) in self._eval_methods:
            if node.__class__ is ntype:
                try:
                    return evaluator(node)
                except ZeroDivisionError as err:
                    raise EvaluationException("zero division", inner=err)
                except ValueError as err:
                    raise EvaluationException("value error", inner=err)
        else:
            raise EvaluationException("invalid inputs")     # unsupported node type, should never happen

    def evaluate(self, exp_or_node: Union[str, nodes.ExpNode]) -> TypeEvalResult:
        """
        parse and evaluate given expression, if the input is a node tree, evaluate it directly
        """

        if isinstance(exp_or_node, nodes.ExpNode):
            exp_tree = exp_or_node
        else:
            exp_tree = parser.parse_expression(exp_or_node)

        return self._eval_node(exp_tree)
