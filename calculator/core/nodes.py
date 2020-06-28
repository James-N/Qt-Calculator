from typing import Union, List


__all__ = ['ExpNode', 'BinaryOpNode', 'UnaryOpNode', 'NumberNode', 'NameConstantNode', 'FuncCallNode']

class ExpNode(object):
    """
    base class for all type of expression nodes
    """

    def __init__(self, pos=0):
        self.pos = pos

    def __str__(self):
        return f'ExpNode()'

class BinaryOpNode(ExpNode):
    """
    node for binary operation like '*', '+', etc
    """

    def __init__(self, op: str, left: ExpNode, right: ExpNode, pos=0):
        super().__init__(pos=pos)

        self.op = op
        self.left = left
        self.right = right

    def __str__(self):
        return f'BinaryOpNode({self.op}, {self.left}, {self.right})'

class UnaryOpNode(ExpNode):
    """
    node for unary operation like '+', '-'
    """

    def __init__(self, op: str, child: ExpNode, pos=0):
        super().__init__(pos=pos)

        self.op = op
        self.child = child

    def __str__(self):
        return f'UnaryOpNode({self.op}, {self.child})'

class NumberNode(ExpNode):
    """
    node for a number literal
    """

    def __init__(self, num: Union[int, float], pos=0):
        super().__init__(pos=pos)

        self.num = num

    def __str__(self):
        return f'NumberNode({self.num})'

class NameConstantNode(ExpNode):
    """
    node for a constant name, like 'e'
    """

    def __init__(self, name: str, pos=0):
        super().__init__(pos=pos)

        self.name = name

    def __str__(self):
        return f'NameConstantNode({self.name})'

class FuncCallNode(ExpNode):
    """
    node for function invocation
    """

    def __init__(self, id_: str, args: List[ExpNode], pos=0):
        super().__init__(pos=pos)

        self.id = id_
        self.args = args

    def __str__(self):
        arg = ', '.join(str(a) for a in self.args)
        return f'FuncCall({self.id}, args=[{args}])'
