from typing import Union

from calculator.core.constants import Separators


__all__ = ['Token', 'TokenName', 'TokenNumber', 'TokenSymbol', 'TokenOpenBracket', 'TokenCloseBracket']

class Token(object):
    """
    base class for token
    """

    def __init__(self, pos=0):
        self.pos = pos

    def __str__(self):
        return f'{self.__class__.__name__}(pos={self.pos})'

class TokenName(Token):
    """
    naming constant token, like π, e, etc
    """

    def __init__(self, name: str, pos=0):
        super().__init__(pos=pos)

        if not isinstance(name, str):
            raise TypeError("name must be str")

        if name == '':
            raise ValueError("name is empty")

        self.name = name

    def __str__(self):
        return f'TokenName({self.name}, pos={self.pos})'

class TokenNumber(Token):
    """
    number token, including 5, 5.5, 5e10
    """

    def __init__(self, num: Union[int, float], pos=0):
        super().__init__(pos=pos)

        if not isinstance(num, (int, float)):
            raise TypeError("num must be number")

        self.num = num

    def __str__(self):
        return f'TokenNumber({self.num}, pos={self.pos})'

class TokenSymbol(Token):
    """
    token for symbol, like '+', '*', '(', etc
    """

    def __init__(self, symbol: str, pos=0):
        super().__init__(pos=pos)

        if not isinstance(symbol, str):
            raise TypeError("symbol must be string")

        if symbol == '':
            raise ValueError("symbol is empty")

        self.symbol = symbol

    def __str__(self):
        return f'TokenSymbol(\'{self.symbol}\', pos={self.pos})'

class TokenOpenBracket(TokenSymbol):
    """
    left bracket
    """

    def __init__(self, pos=0):
        super().__init__(Separators.SEP_LEFT_BRACKET, pos=pos)

class TokenCloseBracket(TokenSymbol):
    """
    right bracket
    """

    def __init__(self, pos=0):
        super().__init__(Separators.SEP_RIGHT_BRACKET, pos=pos)
