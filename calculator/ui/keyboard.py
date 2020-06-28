import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt, pyqtSlot

import calculator.ui.config as config
import calculator.ui.util as util


class CalculatorKeyboardButton(QtWidgets.QAbstractButton):
    """
    keyboard button
    """

    # shape flags
    ROUNDED_CORNER_BOTTOM_LEFT = 1
    ROUNDED_CORNER_BOTTOM_RIGHT = 2

    def __init__(self, text='', size=None, parent=None):
        super().__init__(parent=parent)

        if size is not None:
            self.setFixedSize(size[0], size[1])

        # enable hover
        self.setAttribute(Qt.WA_Hover)

        # update text
        self.setText(text)
        self._textCache = QtGui.QStaticText(text)

        # state color map
        self._states = {
            'default': config.KEYBOARD_BG_DEFAULT,
            'hover': config.KEYBOARD_BG_HOVER
        }
        # current state
        self._currentState = 'default'

        # background transition object
        self._bgColorTransition = None

        # current shape flag
        self._shape = 0

    def setShape(self, shape):
        """
        set shape flag
        """

        self._shape = shape

    def setColor(self, stateName, color):
        """
        set color of sepcified state
        """

        self._states[stateName] = color

    @pyqtSlot()
    def _onTransitionEnd(self):
        self._bgColorTransition = None

    def _changeState(self, target):
        # when state is changed, start background color transition
        # if unfinished transition exists, stop it first

        if target != self._currentState:
            if self._bgColorTransition is None:
                startColor = self._states[self._currentState]
            else:
                startColor = self._bgColorTransition.currentValue().value()
                self._bgColorTransition.stop()
                self._bgColorTransition = None

            animation = QtCore.QVariantAnimation(self)
            animation.setStartValue(startColor)
            animation.setEndValue(self._states[target])
            animation.setDuration(80)

            self._bgColorTransition = animation

            animation.valueChanged.connect(self.repaint)
            animation.destroyed.connect(self._onTransitionEnd)

            self._currentState = target
            animation.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    # event handles #

    def event(self, event):
        # update state according to event
        evtType = event.type()
        if evtType == QtCore.QEvent.HoverEnter:
            self._changeState('hover')
        elif evtType == QtCore.QEvent.HoverLeave:
            self._changeState('default')

        return super().event(event)

    def paintEvent(self, event):
        # decide color from transition and state
        if self._bgColorTransition:
            color = self._bgColorTransition.currentValue()
            if color is None:
                color = self._states[self._currentState]
        else:
            color = self._states[self._currentState]

        # initiate painter
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)

        # draw button shape
        rect = QtCore.QRectF(self.rect())

        if self._shape > 0:
            rSize = config.WINDOW_ROUND_RADIUS - 2
            path = util.createRoundRectPath(
                rect,
                0,
                0,
                rSize if self._shape & CalculatorKeyboardButton.ROUNDED_CORNER_BOTTOM_RIGHT else 0,
                rSize if self._shape & CalculatorKeyboardButton.ROUNDED_CORNER_BOTTOM_LEFT else 0
            )
            painter.drawPath(path)
        else:
            painter.drawRect(rect)

        # draw button text
        textPen = QtGui.QPen(config.KEYBOARD_FG_DEFAULT, 1, Qt.SolidLine)
        painter.setPen(textPen)

        text = self._textCache
        text.prepare(QtGui.QTransform(), painter.font())
        textSize = text.size().toSize()
        painter.drawStaticText(
            (rect.width() - textSize.width()) / 2,
            (rect.height() - textSize.height()) / 2,
            text
        )

class CalculatorKeyboard(QtWidgets.QWidget):
    """
    calculator keyboard, manage set of keyboar buttons
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # config main layout
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 3, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # crate a frame for keyboard background
        frame = QtWidgets.QFrame(parent=self)
        frame.setLineWidth(0)
        frame.setFrameStyle(QtWidgets.QFrame.NoFrame)
        layout.addWidget(frame)

        # create keyboard layout
        frameLayout = QtWidgets.QGridLayout()
        frameLayout.setContentsMargins(0, 0, 0, 0)
        frameLayout.setSpacing(1)
        frame.setLayout(frameLayout)

        self._keyboardGrid = frameLayout
        self._btnSize = None

    def addButton(self, button, row, column):
        """
        add a button to given grid coordinate, the button must be CalculatorKeyboardButton
        """
        if button is None:
            raise ValueError("button is null")

        if not isinstance(button, CalculatorKeyboardButton):
            raise TypeError("invalid keyboard button")

        self._keyboardGrid.addWidget(button, row, column)

        # set button size if override size is given
        if self._btnSize is not None:
            button.setFixedSize(*self._btnSize)

    def setButtonSize(self, size):
        """
        set override button size, all keyboard buttons will be set to this size.\n
        use None to discard any override size.
        """

        if size is None:
            self._btnSize = None
        else:
            self._btnSize = (size[0], size[1])
