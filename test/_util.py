import inspect

from calculator.core.nodes import *

class NodeComparator(object):
    def __init__(self, ignore_pos=False):
        self.ignore_pos = ignore_pos

    def compare_BinaryOpNode(self, n1: BinaryOpNode, n2: BinaryOpNode) -> bool:
        if n1.op == n2.op:
            return self.compare(n1.left, n2.left) and self.compare(n1.right, n2.right)
        else:
            return False

    def compare_UnaryOpNode(self, n1: UnaryOpNode, n2: UnaryOpNode) -> bool:
        if n1.op == n2.op:
            return self.compare(n1.child, n2.child)
        else:
            return False

    def compare_NumberNode(self, n1: NumberNode, n2: NumberNode) -> bool:
        return n1.num == n2.num

    def compare_NameConstantNode(self, n1: NameConstantNode, n2: NameConstantNode) -> bool:
        return n1.name == n2.name

    def compare_FuncCallNode(self, n1: FuncCallNode, n2: FuncCallNode) -> bool:
        if n1.id == n2.id:
            if len(n1.args) == len(n2.args):
                for (a1, a2) in zip(n1.args, n2.args):
                    if not self.compare(a1, a2):
                        return False
                else:
                    return True
            else:
                return False
        else:
            return False

    def compare(self, n1: ExpNode, n2: ExpNode) -> bool:
        if n1 is n2:
            return True
        elif n1 is None:
            return n2 is None
        elif n2 is None:
            return n1 is None
        else:
            c1 = n1.__class__
            c2 = n2.__class__

            if c1 is c2 and issubclass(c1, ExpNode):
                if self.ignore_pos or n1.pos == n2.pos:
                    method = getattr(self, f'compare_{c1.__name__}', None)
                    if method is None:
                        return False
                    else:
                        return method(n1, n2)
                else:
                    return False
            else:
                return False
