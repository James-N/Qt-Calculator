import sys
import re
import math
from abc import ABCMeta, abstractmethod
from typing import Union, Optional, List, Tuple

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QObject

import calculator.ui.config as config
from calculator.core.evaluator import Evaluator, EvaluatorContext
from calculator.core.exception import EvaluationException


ZERO = '0'
DOT = '.'


def formatNumber(n: Union[float, int], maxPrecision: int, roundPrecision: int) -> str:
    """
    custom number formatting
    """

    if maxPrecision > 0:
        exp = 10 ** maxPrecision
        n = round(n * exp) / exp

    if roundPrecision > 0:
        nround = round(n, roundPrecision)
        if math.isclose(nround, n, rel_tol=10**(-roundPrecision)):
            n = nround

    s = str(n)
    if DOT in s:
        s = s.rstrip(ZERO)
        if s[-1] == DOT:
            return s[:-1]
        else:
            return s
    else:
        return s

def checkFunc(content: str) -> str:
    """
    get name of the function if the given content meets function invokation pattern
    """

    match = re.match(r'(\w+)\(.+\)', content)
    if match:
        return match.group(1)
    else:
        return ''


class KeyOption(object):
    """
    keyboard button option
    """

    def __init__(self, text: str, **kwargs):
        self.text = text
        self.fontBold = kwargs.get('fontBold', False)
        self.buttonColor = kwargs.get('buttonColor', None)
        self.fontSize = kwargs.get('fontSize', config.KEY_DEFAULT_FONTSIZE)
        self.hoverColor = kwargs.get('hoverColor', None)
        self.callback = kwargs.get('callback', None)

        size = kwargs.get('size', -1)
        if size > 0:
            self.width = self.height = size
        else:
            self.width = kwargs.get('width', 0)
            self.height = kwargs.get('height', 0)

class CalculatorRuntime(object, metaclass=ABCMeta):
    """
    abstract base class for calculator runtime
    """

    def __init__(self):
        self.__model = CalculatorRuntimeModel(self)

    @property
    def model(self):
        """
        get runtime model
        """
        return self.__model

    @model.setter
    def model(self, value):
        raise RuntimeError("cannot change model property")

    @abstractmethod
    def justEvaluated(self) -> bool:
        """
        whether an evaluation was just performed
        """
        return False

    @abstractmethod
    def isError(self) -> bool:
        """
        whether an error occurred during evaluation
        """
        return False

    @abstractmethod
    def reset(self):
        """
        reset runtime state
        """
        return

    @abstractmethod
    def getKeyboard(self) -> List[List[KeyOption]]:
        """
        get keyboard table
        """
        raise NotImplementedError()

    @abstractmethod
    def getKeyboardDimension(self) -> Tuple[int, int, int, int]:
        """
        get (column count, row count, key width, key height) of keyboard
        """
        raise NotImplementedError()

    @abstractmethod
    def onKeyboardEvent(self, event):
        """
        process keyboard event
        """
        return

class CalculatorRuntimeModel(QObject):
    """
    model object for runtime
    """

    # model change signal
    modelChange = pyqtSignal([], [CalculatorRuntime])

    def __init__(self, runtime: CalculatorRuntime):
        super().__init__()

        self._runtime = runtime

        self.__hint = ''
        self.__input = ZERO

    def _triggerChangeSignal(self):
        self.modelChange.emit()
        self.modelChange[CalculatorRuntime].emit(self._runtime)

    @property
    def hint(self) -> str:
        """
        get hint (secondary input) content
        """
        return self.__hint

    @hint.setter
    def hint(self, value: str):
        """
        set hint content
        """

        if value != self.__hint:
            self.__hint = value
            self._triggerChangeSignal()

    @property
    def input(self) -> str:
        """
        get input (primary input) content
        """
        return self.__input

    @input.setter
    def input(self, value: str):
        """
        set input content
        """

        if value != self.__input:
            self.__input = value
            self._triggerChangeSignal()

    def reset(self, noSignal=False):
        """
        reset model state, clear all the contents
        """

        hasChange = False

        if self.__input != ZERO:
            self.__input = ZERO
            hasChange = True

        if self.__hint != '':
            self.__hint = ''
            hasChange = True

        if (not noSignal) and hasChange:
            self._triggerChangeSignal()

    def update(self, input_: str, hint: str):
        """
        set input and hint at the same time
        """

        hasChange = False

        if self.__input != input_:
            self.__input = input_
            hasChange = True

        if self.__hint != hint:
            self.__hint = hint
            hasChange = True

        if hasChange:
            self._triggerChangeSignal()


class StdRTStates(object):
    """
    states enums for standard runtime
    """

    ANY = 1
    BINOP = 2
    PREOP = 3
    POSTOP = 4
    FUNC = 5
    L_BRACKET = 6
    R_BRACKET = 7
    CONST = 8
    EVAL = 20
    ERROR = 21

class CalculatorRuntimeStandard(CalculatorRuntime, metaclass=ABCMeta):
    """
    partial implementation of standard runtime
    """

    def __init__(self, evaluator=None):
        super().__init__()

        self._evaluator = evaluator

        # stack of states for current input
        self._stateStack = [StdRTStates.ANY]

        self._uncloseBrackets = 0

        # key maps
        self._keyMap = {}

    ### state management ###

    def _setState(self, code):
        if code in (StdRTStates.EVAL, StdRTStates.ERROR, StdRTStates.BINOP):
            # once the new op is EVAL/ERROR/BINOP, the input field will be rewinded,
            # in which case the current state stack can be discarded
            self._resetState()

        if code != StdRTStates.ANY or code != self._peekState():
            if code == StdRTStates.BINOP:
                self._stateStack.append(code)
            else:
                if self._peekState() == StdRTStates.BINOP:
                    # once a new op other than BINOP is added
                    # an ANYOP should be inserted after previous BINOP
                    # to barrier further operations
                    self._stateStack.append(StdRTStates.ANY)

                self._stateStack.append(code)

    def _peekState(self):
        """
        check the topest state
        """
        return self._stateStack[-1]

    def _matchState(self, *codes):
        """
        check whether the topest state match any of the given states
        """
        return self._peekState() in codes

    def _popState(self):
        """
        remove and return the topest state
        """

        if len(self._stateStack) > 1:
            return self._stateStack.pop()
        else:
            return self._peekState()

    def _popTopMostState(self, code) -> bool:
        """
        remove the topest state that matches the given code
        """

        stack = self._stateStack
        if len(stack) > 1:
            i = len(stack) - 1
            while (i > 1):
                if stack[i] == code:
                    stack.pop(i)
                    if i < len(stack):
                        # merge neighbour ANYOPs
                        if stack[i] == StdRTStates.ANY and stack[i - 1] == StdRTStates.ANY:
                            stack.pop(i)
                    return True
            else:
                return False
        else:
            return False

    def _resetState(self):
        """
        unconditionally reset all states
        """
        self._stateStack = [StdRTStates.ANY]

    def _clearEval(self):
        """
        clear evaluation state and model
        """

        if self.justEvaluated():
            self.model.hint = ''
            # once current state is just evaluated
            # the stack should be like [ANYOP, EVAL]
            self._popState()

    def _clearInput(self):
        """
        clear current input and remove associated states
        """

        for s in self._stateStack:
            if s == StdRTStates.R_BRACKET:
                self._uncloseBrackets += 1

        self.model.input = ZERO
        self._resetState()

    def reset(self):
        self.model.reset()
        self._resetState()
        self._uncloseBrackets = 0

    ### state query ###

    def _canChangeNumber(self):
        return not self._matchState(
            StdRTStates.POSTOP, StdRTStates.FUNC, StdRTStates.CONST, StdRTStates.R_BRACKET, StdRTStates.POSTOP
        )

    def _canEvaluate(self):
        if self._matchState(StdRTStates.EVAL, StdRTStates.ERROR):
            return False
        elif self.model.hint != '':
            return True
        else:
            for s in reversed(self._stateStack):
                if s != StdRTStates.ANY and s != StdRTStates.PREOP:
                    return True
            else:
                return False

    def justEvaluated(self):
        return self._peekState() == StdRTStates.EVAL

    def isError(self):
        return self._peekState() == StdRTStates.ERROR

    ### handles ###

    def _clearHandle(self):
        self.reset()

    def _inputClearHandle(self):
        if self.justEvaluated():
            self.reset()
        else:
            self._clearInput()

    def _eraseHandle(self):
        current = self.model.input
        state = self._peekState()

        if self.isError():
            self.reset()
        elif state == StdRTStates.FUNC:
            # remove the outest function call
            funcName = checkFunc(current)
            current = current[len(funcName) + 1 : -1]
            self.model.input = current
            self._popState()
        elif state == StdRTStates.PREOP:
            self.model.input = current[1:]
            self._popState()
        elif state == StdRTStates.POSTOP:
            self.model.input = current[:-1]
            self._popState()
        elif state == StdRTStates.R_BRACKET:
            self.model.input = current[:-1]
            self._popState()
            self._uncloseBrackets += 1
        else:
            self._clearEval()

            if len(current) > 1:
                current = current[:-1]
                # if the only lefted char is not number, clear anyway
                if len(current) == 1 and not current.isnumeric():
                    current = ZERO

                self.model.input = current
                self._setState(StdRTStates.ANY)
            else:
                self.model.input = ZERO
                self._setState(StdRTStates.ANY)

    def _numberHandle(self, number):
        if self._canChangeNumber():
            model = self.model

            if self.justEvaluated() or self.isError():
                model.update(number, '')
            else:
                if number == ZERO:
                    if model.input != ZERO:
                        model.input += ZERO
                else:
                    if model.input == ZERO:
                        model.input = number
                    else:
                        model.input += number

            self._setState(StdRTStates.ANY)

    def _getNumberHandle(self, number):
        number = str(number)

        @pyqtSlot()
        def numberHandle():
            self._numberHandle(number)

        return numberHandle

    def _dotHandle(self):
        if not self.isError() and self._canChangeNumber():
            model = self.model
            if self.justEvaluated():
                model.update('0.', '')
                self._setState(StdRTStates.ANY)
            if DOT not in self.model.input:
                self.model.input += DOT
                self._setState(StdRTStates.ANY)

    def _constantHandle(self, name):
        # constant will replace current input
        if self.isError() or self.justEvaluated():
            self.reset()
        else:
            self._clearInput()

        self.model.input = name
        self._setState(StdRTStates.CONST)

    def _getConstantHandle(self, name):
        @pyqtSlot()
        def constHandle():
            self._constantHandle(name)

        return constHandle

    def _binaryOpHandle(self, op):
        if not self.isError():
            model = self.model
            if self._peekState() == StdRTStates.BINOP:
                # if the immediate previous operation is also BINOP, replace it
                model.hint = model.hint[:-1] + op
            else:
                if self.justEvaluated():
                    model.update(ZERO, f'{model.input} {op}')
                else:
                    # perform simple formatting
                    hint = model.hint if model.hint.endswith('(') else (model.hint + ' ')
                    model.update(ZERO, f'{hint}{model.input} {op}')
                self._setState(StdRTStates.BINOP)

    def _getBinaryOpHandle(self, op):
        """
        get binary op handle
        """

        @pyqtSlot()
        def handle():
            self._binaryOpHandle(op)

        return handle

    def _negetHandle(self):
        if not self.isError():
            model = self.model

            self._clearEval()

            if model.input != ZERO:
                # toggle '-' operator on/off
                if model.input[0] == '-':
                    model.input = model.input[1:]
                    self._popTopMostState(StdRTStates.PREOP)
                else:
                    model.input = '-' + model.input
                    self._setState(StdRTStates.PREOP)

    def _factorialHandle(self):
        if not self.isError() and self._peekState() != StdRTStates.POSTOP:
            self._clearEval()

            self.model.input += '!'
            self._setState(StdRTStates.POSTOP)

    def _unaryFuncHandle(self, func):
        if not self.isError() and self._peekState() != StdRTStates.R_BRACKET:
            model = self.model

            self._clearEval()

            model.input = f'{func}({model.input})'
            self._setState(StdRTStates.FUNC)

    def _getUnaryFuncHandle(self, func):
        """
        get unary function handle
        """
        @pyqtSlot()
        def handle():
            self._unaryFuncHandle(func)

        return handle

    def _leftBracketHandle(self):
        if not self.isError():
            self._clearEval()

            model = self.model
            # left bracket won't appear in input, append it to hint directly
            if model.hint == '':
                model.hint = '('
            else:
                model.hint += ' ('
                if self._peekState() == StdRTStates.BINOP:
                    self._popState()

            self._uncloseBrackets += 1

    def _rightBracketHandle(self):
        if self._uncloseBrackets > 0:
            self.model.input += ')'
            self._uncloseBrackets -= 1

            self._setState(StdRTStates.R_BRACKET)

    def evaluate(self):
        def checkInnerErrType(err, cls):
            return err.inner is not None and isinstance(err.inner, cls)

        if self._canEvaluate():
            model = self.model
            if model.hint == '':
                expr = model.input
            else:
                expr = model.hint + ' ' + model.input

            # complement unmatched left brackets
            if self._uncloseBrackets > 0:
                expr += (')' * self._uncloseBrackets)

            try:
                output = self._evaluator.evaluate(expr)
                # model.update(f'{output:.20g}', expr + ' =')
                model.update(formatNumber(output, 16, 12), expr + ' =')
                self._setState(StdRTStates.EVAL)
            except Exception as err:
                sys.stdout.write(f"error occurred during evaluation: {err}\n")

                if isinstance(err, EvaluationException):
                    if checkInnerErrType(err, ZeroDivisionError):
                        model.update('ERROR: Zero Division', '')
                    elif checkInnerErrType(err, ValueError):
                        model.update('ERROR: Invalid Input', '')
                    else:
                        model.update('ERROR', '')
                else:
                    model.update('ERROR', '')

                self._setState(StdRTStates.ERROR)
            finally:
                self._uncloseBrackets = 0

    # keyboard event handle
    def onKeyboardEvent(self, event):
        def triggerFromKeyMap(key, modifier):
            key = self._keyMap.get(key)
            if key is not None:
                m, cb, *args = key
                if isinstance(m, tuple):
                    accept = modifier in m
                else:
                    accept = m == modifier

                if accept:
                    cb(*args)

        modifiers = event.modifiers()
        key = event.key()

        if modifiers == Qt.NoModifier or modifiers == Qt.KeypadModifier:
            if Qt.Key_0 <= key <= Qt.Key_9:
                self._numberHandle(str(key - Qt.Key_0))
            elif key == Qt.Key_Return or key == Qt.Key_Enter or key == Qt.Key_Equal:
                self.evaluate()
            else:
                triggerFromKeyMap(key, modifiers)
        elif modifiers == Qt.ShiftModifier:
            triggerFromKeyMap(key, modifiers)


class CalculatorRuntimeBasic(CalculatorRuntimeStandard):
    """
    basic runtime, given most necessary keys
    """

    def __init__(self):
        super().__init__()

        functions = {
            'invert': lambda a: 1 / a
        }
        context = EvaluatorContext(functions=functions)
        self._evaluator = Evaluator(context)

        self._keyMap = {
            Qt.Key_Period: ((Qt.NoModifier, Qt.KeypadModifier), self._dotHandle),
            Qt.Key_Backspace: (Qt.NoModifier, self._eraseHandle),
            Qt.Key_Escape: (Qt.NoModifier, self._clearHandle),
            Qt.Key_Plus: ((Qt.ShiftModifier, Qt.KeypadModifier), self._binaryOpHandle, '+'),
            Qt.Key_Minus: ((Qt.NoModifier, Qt.KeypadModifier), self._binaryOpHandle, '-'),
            Qt.Key_Asterisk: ((Qt.ShiftModifier, Qt.KeypadModifier), self._binaryOpHandle, '×'),
            Qt.Key_Slash: ((Qt.ShiftModifier, Qt.KeypadModifier), self._binaryOpHandle, '÷')
        }

    def getKeyboard(self):
        keySize = config.KEY_SIZE_STD

        return [
            [
                KeyOption('AC', fontSize=20, size=keySize, hoverColor=config.KEY_DANGER_BG_HOVER, callback=self._clearHandle),
                KeyOption('+/-', size=keySize, callback=self._negetHandle),
                KeyOption('1 / x', fontSize=18, size=keySize, callback=self._getUnaryFuncHandle('invert')),
                KeyOption('÷', fontSize=24, size=keySize, callback=self._getBinaryOpHandle('÷'))
            ],
            [
                KeyOption('7', size=keySize, callback=self._getNumberHandle(7)),
                KeyOption('8', size=keySize, callback=self._getNumberHandle(8)),
                KeyOption('9', size=keySize, callback=self._getNumberHandle(9)),
                KeyOption('×', fontSize=24, size=keySize, callback=self._getBinaryOpHandle('×'))
            ],
            [
                KeyOption('4', size=keySize, callback=self._getNumberHandle(4)),
                KeyOption('5', size=keySize, callback=self._getNumberHandle(5)),
                KeyOption('6', size=keySize, callback=self._getNumberHandle(6)),
                KeyOption('-', fontSize=35, size=keySize, callback=self._getBinaryOpHandle('-'))
            ],
            [
                KeyOption('1', size=keySize, callback=self._getNumberHandle(1)),
                KeyOption('2', size=keySize, callback=self._getNumberHandle(2)),
                KeyOption('3', size=keySize, callback=self._getNumberHandle(3)),
                KeyOption('+', fontSize=24, size=keySize, callback=self._getBinaryOpHandle('+'))
            ],
            [
                KeyOption('0', size=keySize, callback=self._getNumberHandle(0)),
                KeyOption('.', fontBold=True, size=keySize, callback=self._dotHandle),
                KeyOption('DEL', fontSize=18, size=keySize, callback=self._eraseHandle),
                KeyOption('=', fontSize=28, fontBold=True, buttonColor=config.KEY_EVAL_BG_DEFAULT, hoverColor=config.KEY_EVAL_BG_HOVER, size=keySize,
                    callback=self.evaluate)
            ]
        ]

    def getKeyboardDimension(self):
        return (4, 5, config.KEY_SIZE_STD, config.KEY_SIZE_STD)

class CalculatorRuntimePro(CalculatorRuntimeStandard):
    def __init__(self):
        super().__init__()

        functions = {
            'sqrt': math.sqrt,
            'square': lambda a: a * a,
            'cube': lambda a: a * a * a,
            'degree': math.degrees,
            'radians': math.radians,
            'sin': math.sin,
            'sind': lambda d: math.sin(math.radians(d)),
            'cos': math.cos,
            'cosd': lambda d: math.cos(math.radians(d)),
            'tan': math.tan,
            'tand': lambda d: math.tan(math.radians(d)),
            'log': math.log10,
            'ln': lambda a: math.log(a),        # cannot get spec from math.log directly, maybe a bug
            'exp': math.exp,
            'abs': abs,
            'floor': math.floor,
            'ceil': math.ceil,
            'invert': lambda a: 1 / a
        }
        context = EvaluatorContext(functions=functions)
        self._evaluator = Evaluator(context)

        self._keyMap = {
            Qt.Key_Period: ((Qt.NoModifier, Qt.KeypadModifier), self._dotHandle,),
            Qt.Key_Backspace: (Qt.NoModifier, self._eraseHandle,),
            Qt.Key_Escape: (Qt.NoModifier, self._clearHandle,),
            Qt.Key_Plus: ((Qt.ShiftModifier, Qt.KeypadModifier), self._binaryOpHandle, '+'),
            Qt.Key_Minus: ((Qt.NoModifier, Qt.KeypadModifier), self._binaryOpHandle, '-'),
            Qt.Key_Asterisk: ((Qt.ShiftModifier, Qt.KeypadModifier), self._binaryOpHandle, '×'),
            Qt.Key_Slash: ((Qt.ShiftModifier, Qt.KeypadModifier), self._binaryOpHandle, '÷'),
            Qt.Key_ParenLeft: (Qt.ShiftModifier, self._leftBracketHandle),
            Qt.Key_ParenRight: (Qt.ShiftModifier, self._rightBracketHandle),
            Qt.Key_Exclam: (Qt.ShiftModifier, self._factorialHandle),
            Qt.Key_Percent: (Qt.ShiftModifier, self._binaryOpHandle, '%'),
            Qt.Key_AsciiCircum: (Qt.ShiftModifier, self._binaryOpHandle, '^'),
            Qt.Key_E: (Qt.NoModifier, self._constantHandle, 'e'),
            Qt.Key_P: (Qt.NoModifier, self._constantHandle, 'π')
        }

    def getKeyboard(self):
        keyboard = [
            [
                KeyOption('+/-', callback=self._negetHandle),
                KeyOption('AC', fontSize=20, hoverColor=config.KEY_DANGER_BG_HOVER, callback=self._clearHandle),
                KeyOption('C', fontSize=20, callback=self._inputClearHandle),
                KeyOption('%', fontSize=18, callback=self._getBinaryOpHandle('%')),
                KeyOption('÷', callback=self._getBinaryOpHandle('÷')),
                KeyOption('sqrt', fontSize=18, callback=self._getUnaryFuncHandle('sqrt')),
                KeyOption('deg', fontSize=18, callback=self._getUnaryFuncHandle('degree')),
                KeyOption('sin', fontSize=18, callback=self._getUnaryFuncHandle('sin')),
                KeyOption('sin°', fontSize=18, callback=self._getUnaryFuncHandle('sind'))
            ],
            [
                KeyOption('1 / x', fontSize=20, callback=self._getUnaryFuncHandle('invert')),
                KeyOption('7', callback=self._getNumberHandle(7)),
                KeyOption('8', callback=self._getNumberHandle(8)),
                KeyOption('9', callback=self._getNumberHandle(9)),
                KeyOption('×', callback=self._getBinaryOpHandle('×')),
                KeyOption('x<sup> y</sup>', fontSize=18, callback=self._getBinaryOpHandle('^')),
                KeyOption('rad', fontSize=18, callback=self._getUnaryFuncHandle('radians')),
                KeyOption('cos', fontSize=18, callback=self._getUnaryFuncHandle('cos')),
                KeyOption('cos°', fontSize=18, callback=self._getUnaryFuncHandle('cosd'))
            ],
            [
                KeyOption('π', fontSize=20, callback=self._getConstantHandle('π')),
                KeyOption('4', callback=self._getNumberHandle(4)),
                KeyOption('5', callback=self._getNumberHandle(5)),
                KeyOption('6', callback=self._getNumberHandle(6)),
                KeyOption('-', fontSize=30, callback=self._getBinaryOpHandle('-')),
                KeyOption('x<sup> 2</sup>', fontSize=18, callback=self._getUnaryFuncHandle('square')),
                KeyOption('log', fontSize=18, callback=self._getUnaryFuncHandle('log')),
                KeyOption('tan', fontSize=18, callback=self._getUnaryFuncHandle('tan')),
                KeyOption('tan°', fontSize=18, callback=self._getUnaryFuncHandle('tand'))
            ],
            [
                KeyOption('e', fontSize=20, callback=self._getConstantHandle('e')),
                KeyOption('1', callback=self._getNumberHandle(1)),
                KeyOption('2', callback=self._getNumberHandle(2)),
                KeyOption('3', callback=self._getNumberHandle(3)),
                KeyOption('+', callback=self._getBinaryOpHandle('+')),
                KeyOption('x<sup> 3</sup>', fontSize=18, callback=self._getUnaryFuncHandle('cube')),
                KeyOption('ln', fontSize=18, callback=self._getUnaryFuncHandle('ln')),
                KeyOption('floor', fontSize=18, callback=self._getUnaryFuncHandle('floor')),
                KeyOption('|x|', fontSize=18, callback=self._getUnaryFuncHandle('abs'))
            ],
            [
                KeyOption('(', fontSize=20, callback=self._leftBracketHandle),
                KeyOption(')', fontSize=20, callback=self._rightBracketHandle),
                KeyOption('0', callback=self._getNumberHandle(0)),
                KeyOption('.', fontBold=True, callback=self._dotHandle),
                KeyOption('DEL', fontSize=18, callback=self._eraseHandle),
                KeyOption('n!', fontSize=20, callback=self._factorialHandle),
                KeyOption('e<sup> x</sup>', fontSize=18, callback=self._getUnaryFuncHandle('exp')),
                KeyOption('ceil', fontSize=18, callback=self._getUnaryFuncHandle('ceil')),
                KeyOption('=', fontBold=True, buttonColor=config.KEY_EVAL_BG_DEFAULT, hoverColor=config.KEY_EVAL_BG_HOVER, callback=self.evaluate)
            ]
        ]

        for row in keyboard:
            for key in row:
                key.width = config.KEY_WIDTH_PRO
                key.height = config.KEY_HEIGHT_PRO

                if isinstance(key.text, str) and (key.text.isnumeric() or key.text == '.'):
                    key.hoverColor = config.KEY_SPECIAL_BG_HOVER

        return keyboard

    def getKeyboardDimension(self):
        return (9, 5, config.KEY_WIDTH_PRO, config.KEY_HEIGHT_PRO)
