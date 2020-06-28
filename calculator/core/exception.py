__all__ = ['ParsingException']

class ParsingException(Exception):
    """
    error for expression parsing
    """

    def __init__(self, msg: str, pos=-1):
        super().__init__(msg, pos)

        self.pos = pos + 1

class EvaluationException(Exception):
    """
    error for expression evaluation
    """

    def __init__(self, msg: str, inner: Exception = None):
        super().__init__(msg)

        self.inner = inner
