from calculator.core.constants import OperatorAffix

__all__ = ['OperatorInfo']

class OperatorInfo(object):
    """
    info object for expression operators
    """

    def __init__(self, op: str, priority: int, affix: OperatorAffix = OperatorAffix.INFIX):
        self.op = op
        self.priority = priority
        self.affix = affix
