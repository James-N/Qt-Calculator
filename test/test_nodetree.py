import unittest

import calculator.core.parser as parser
from calculator.core.nodes import *
from calculator.core.exception import ParsingException

from _util import NodeComparator


class NodeTreeTest(unittest.TestCase):
    @staticmethod
    def _to_node_tree(exp):
        tokens = parser.tokenize(exp)
        return parser.build_expression_tree(tokens)

    def setUp(self):
        self.node_comparator = NodeComparator()

    def test_basic_parsing(self):
        node = NodeTreeTest._to_node_tree('1 + 2 × 3')

        ref_node = BinaryOpNode(
            '+',
            NumberNode(1, pos=0),
            BinaryOpNode(
                '×',
                NumberNode(2, pos=4),
                NumberNode(3, pos=8),
                pos=6
            ),
            pos=2
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

        node = NodeTreeTest._to_node_tree('1.1 ÷ 0.5 - 4 × 2')
        ref_node = BinaryOpNode(
            '-',
            BinaryOpNode(
                '÷',
                NumberNode(1.1, pos=0),
                NumberNode(0.5, pos=6),
                pos=4
            ),
            BinaryOpNode(
                '×',
                NumberNode(4, pos=12),
                NumberNode(2, pos=16),
                pos=14
            ),
            pos=10
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

        node = NodeTreeTest._to_node_tree('1 ÷ 2 × 3')
        ref_node = BinaryOpNode(
            '×',
            BinaryOpNode(
                '÷',
                NumberNode(1, pos=0),
                NumberNode(2, pos=4),
                pos=2
            ),
            NumberNode(3, pos=8),
            pos=6
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

    def test_bracket_parsing(self):
        node = NodeTreeTest._to_node_tree('(1 + 2) × 3')

        ref_node = BinaryOpNode(
            '×',
            BinaryOpNode(
                '+',
                NumberNode(1, pos=1),
                NumberNode(2, pos=5),
                pos=3
            ),
            NumberNode(3, pos=10),
            pos=8
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

        node = NodeTreeTest._to_node_tree('3 + (2×(-1 + 10)) -5.5')

        ref_node = BinaryOpNode(
            '+',
            NumberNode(3, pos=0),
            BinaryOpNode(
                '-',
                BinaryOpNode(
                    '×',
                    NumberNode(2, pos=5),
                    BinaryOpNode(
                        '+',
                        UnaryOpNode(
                            '-',
                            NumberNode(1, pos=9),
                            pos=8
                        ),
                        NumberNode(10, pos=13),
                        pos=11
                    ),
                    pos=6
                ),
                NumberNode(5.5, pos=19),
                pos=18
            ),
            pos=2
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

    def test_bracket_parsing_special(self):
        node = NodeTreeTest._to_node_tree('((1)) + 2')

        ref_node = BinaryOpNode(
            '+',
            NumberNode(1, pos=2),
            NumberNode(2, pos=8),
            pos=6
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

        node = NodeTreeTest._to_node_tree('-(3 + 1)')

        ref_node = UnaryOpNode(
            '-',
            BinaryOpNode(
                '+',
                NumberNode(3, pos=2),
                NumberNode(1, pos=6),
                pos=4
            ),
            pos=0
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

    def test_bracket_unmatch(self):
        with self.assertRaises(ParsingException) as cm:
            NodeTreeTest._to_node_tree('(1+2 × 3')

        self.assertIn('(', cm.exception.args[0])

        with self.assertRaises(ParsingException) as cm:
            NodeTreeTest._to_node_tree('1 + (1 × 2 + 3)) - 3')

        self.assertIn(')', cm.exception.args[0])

    def test_postfix_unary(self):
        node = NodeTreeTest._to_node_tree('1 + 3! × 2')

        ref_node = BinaryOpNode(
            '+',
            NumberNode(1, pos=0),
            BinaryOpNode(
                '×',
                UnaryOpNode(
                    '!',
                    NumberNode(3, pos=4),
                    pos=5
                ),
                NumberNode(2, pos=9),
                pos=7
            ),
            pos=2
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

        node = NodeTreeTest._to_node_tree('2 + -3!')

        ref_node = BinaryOpNode(
            '+',
            NumberNode(2, pos=0),
            UnaryOpNode(
                '-',
                UnaryOpNode(
                    '!',
                    NumberNode(3, pos=5),
                    pos=6
                ),
                pos=4
            ),
            pos=2
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

        node = NodeTreeTest._to_node_tree('(1 + 2)! ÷ 3')

        ref_node = BinaryOpNode(
            '÷',
            UnaryOpNode(
                '!',
                BinaryOpNode(
                    '+',
                    NumberNode(1, pos=1),
                    NumberNode(2, pos=5),
                    pos=3
                ),
                pos=7
            ),
            NumberNode(3, pos=11),
            pos=9
        )

        with self.assertRaises(ParsingException) as cm:
            NodeTreeTest._to_node_tree('1 + !4')

        self.assertIn('prefix', cm.exception.args[0])

    def test_name_constant(self):
        node = NodeTreeTest._to_node_tree('1 + e^2 - 2')

        ref_node = BinaryOpNode(
            '-',
            BinaryOpNode(
                '+',
                NumberNode(1, pos=0),
                BinaryOpNode(
                    '^',
                    NameConstantNode('e', pos=4),
                    NumberNode(2, pos=6),
                    pos=5
                ),
                pos=2
            ),
            NumberNode(2, pos=10),
            pos=8
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

    def test_basic_func_call(self):
        node = NodeTreeTest._to_node_tree('sin(20)')

        ref_node = FuncCallNode(
            'sin',
            [NumberNode(20, pos=4)],
            pos=0
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

        node = NodeTreeTest._to_node_tree('log(1, 3 × -1.4)')

        ref_node = FuncCallNode(
            'log',
            [
                NumberNode(1, pos=4),
                BinaryOpNode(
                    '×',
                    NumberNode(3, pos=7),
                    UnaryOpNode(
                        '-',
                        NumberNode(1.4, pos=12),
                        pos=11
                    ),
                    pos=9
                )
            ],
            pos=0
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

    def test_complex_func_call(self):
        node = NodeTreeTest._to_node_tree('pow(log(100, 5 × 2), 2)')

        ref_node = FuncCallNode(
            'pow',
            [
                FuncCallNode(
                    'log',
                    [
                        NumberNode(100, pos=8),
                        BinaryOpNode(
                            '×',
                            NumberNode(5, pos=13),
                            NumberNode(2, pos=17),
                            pos=15
                        )
                    ],
                    pos=4
                ),
                NumberNode(2, pos=21)
            ],
            pos=0
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

        node = NodeTreeTest._to_node_tree('1.125×abs(-1)')

        ref_node = BinaryOpNode(
            '×',
            NumberNode(1.125, pos=0),
            FuncCallNode(
                'abs',
                [
                    UnaryOpNode(
                        '-',
                        NumberNode(1, pos=11),
                        pos=10
                    )
                ],
                pos=6
            ),
            pos=5
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

        node = NodeTreeTest._to_node_tree('-sin(2 × π)')

        ref_node = UnaryOpNode(
            '-',
            FuncCallNode(
                'sin',
                [
                    BinaryOpNode(
                        '×',
                        NumberNode(2, pos=5),
                        NameConstantNode('π', pos=9),
                        pos=7
                    )
                ],
                pos=1
            ),
            pos=0
        )

        self.assertTrue(self.node_comparator.compare(node, ref_node))

    def test_invalid_func_call(self):
        with self.assertRaises(ParsingException) as cm:
            NodeTreeTest._to_node_tree('1 + pow(100, 2')

        self.assertIn('unclose func call', cm.exception.args[0])

        with self.assertRaises(ParsingException) as cm:
            NodeTreeTest._to_node_tree('1 + 0(100)')

        self.assertIn('(', cm.exception.args[0])

        try:
            NodeTreeTest._to_node_tree('1 + π(100)')
        except ParsingException:
            self.fail("ParsingException shall not be raised")

        with self.assertRaises(ParsingException) as cm:
            NodeTreeTest._to_node_tree('1+ 1, 2 × 2')

        self.assertIn('unexpected token', cm.exception.args[0])
