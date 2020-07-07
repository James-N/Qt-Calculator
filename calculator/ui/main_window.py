import os.path

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt, QEvent, pyqtSlot

import calculator.ui.config as config
import calculator.ui.font as font
import calculator.ui.util as util
from calculator.ui.keyboard import CalculatorKeyboard, CalculatorKeyboardButton
from calculator.ui.displayer import CalculatorDisplayer
from calculator.ui.runtime import CalculatorRuntime, CalculatorRuntimeBasic, CalculatorRuntimePro


class WindowButton(QtWidgets.QAbstractButton):
    """
    button appears on top of the window
    """

    def __init__(self, iconName, parent=None):
        super().__init__(parent=parent)

        # enable hover
        self.setAttribute(Qt.WA_Hover)

        # set size
        btnSize = config.WINDOW_TOOL_BTN_SIZE
        self.setFixedSize(btnSize, btnSize)

        # set fonts
        self.setFont(font.getIconFont())
        self.setText(font.getIconCode(iconName))
        self.setCursor(Qt.PointingHandCursor)

        # painting components storage
        self._brushes = {}
        self._pens = {}

    def configBackgroundColors(self, colors):
        """
        config background colors for difference states
        """

        for (state, color) in colors.items():
            self._brushes[state] = QtGui.QBrush(QtGui.QColor(color))

    def configForegroundColors(self, colors):
        """
        config text colors for different states
        """

        for (state, color) in colors.items():
            self._pens[state] = QtGui.QPen(QtGui.QColor(color))

    def paintEvent(self, event):
        opt = QtWidgets.QStyleOptionButton()
        opt.initFrom(self)

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # prepare background brush and text pen
        if self.isChecked():
            bgBrush = self._brushes.get(QtWidgets.QStyle.State_On)
            fgPen = self._pens.get(QtWidgets.QStyle.State_On)
        elif self.underMouse():
            bgBrush = self._brushes.get(QtWidgets.QStyle.State_MouseOver)
            fgPen = self._pens.get(QtWidgets.QStyle.State_MouseOver)

            if fgPen is None:
                fgPen = self._pens.get(QtWidgets.QStyle.State_None)
        else:
            bgBrush = self._brushes.get(QtWidgets.QStyle.State_None)
            fgPen = self._pens.get(QtWidgets.QStyle.State_None)

        # save painter state
        painter.save()

        # draw circle shape
        if bgBrush is not None:
            painter.setBrush(bgBrush)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(opt.rect)

        # restore initial painter state
        painter.restore()

        # compute icon position
        fontMetrics = self.fontMetrics()
        charRect = fontMetrics.boundingRect(self.text())

        textRect = QtCore.QRect(
            (opt.rect.width() - charRect.width()) / 2,
            (opt.rect.height() - charRect.height()) / 2,
            charRect.width(),
            charRect.height()
        )

        # draw text icon
        if fgPen is not None:
            painter.setPen(fgPen)
        painter.setBrush(Qt.NoBrush)
        painter.drawText(textRect, Qt.AlignCenter, self.text())

class CalculatorWindowBackboard(QtWidgets.QWidget):
    """
    the actual visual area of the window
    """

    BRUSH_BG = QtGui.QBrush(config.WINDOW_BG)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # dragging states
        self.isDragging = False
        self._draggingCoord = None

        # mode switch flags
        self.proModeEnabled = False

        # main ui components
        self._displayer = None
        self._keyboardBasic = None
        self._keyboardPro = None

        # initiate runtimes
        self._runtimeBasic = CalculatorRuntimeBasic()
        self._runtimeBasic.model.modelChange[CalculatorRuntime].connect(self.onRuntimeModelChange)

        self._runtimePro = CalculatorRuntimePro()
        self._runtimePro.model.modelChange[CalculatorRuntime].connect(self.onRuntimeModelChange)

        # ui initiation
        self._initUI()
        self.installEventFilter(self)

    def _initUI(self):
        # config layout
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addSpacerItem(QtWidgets.QSpacerItem(100, 45))

        # create displayer
        self._displayer = CalculatorDisplayer(parent=self)
        self._displayer.setObjectName("CalculatorDisplayer")
        self._displayer.setPrimaryContent(self._runtimeBasic.model.input)
        layout.addWidget(self._displayer)

        # create basic keyboard
        self._keyboardBasic = CalculatorKeyboard(parent=self)
        self._keyboardBasic.setObjectName("CalculatorKeyboardBasic")
        self._configKeyboard(self._runtimeBasic.getKeyboard(), self._keyboardBasic)
        layout.addWidget(self._keyboardBasic, 10)

        # create pro keyboard
        self._keyboardPro = CalculatorKeyboard(parent=self)
        self._keyboardBasic.setObjectName("CalculatorKeyboardPro")
        self._configKeyboard(self._runtimePro.getKeyboard(), self._keyboardPro)
        layout.addWidget(self._keyboardPro, 10)
        self._keyboardPro.hide()

        # config dropshadow
        dropshadowEffect = QtWidgets.QGraphicsDropShadowEffect(parent=self)
        dropshadowEffect.setOffset(0, 0)
        dropshadowEffect.setBlurRadius(config.WINDOW_DROPSHADOW_RADIUS)
        dropshadowEffect.setColor(config.WINDOW_DROPSHADOW_COLOR)
        self.setGraphicsEffect(dropshadowEffect)

    def _configKeyboard(self, keys, keyboard):
        """
        create keyboard key according to given key array and attach them to keyboard
        """

        for (r, row) in enumerate(keys):
            for (c, key) in enumerate(row):
                key = row[c]
                button = CalculatorKeyboardButton(key.text, size=(key.width, key.height), parent=keyboard)

                # config font
                font = button.font()
                if key.fontBold:
                    font.setWeight(QtGui.QFont.Normal)
                else:
                    font.setWeight(QtGui.QFont.Thin)

                font.setPixelSize(key.fontSize)
                button.setFont(font)

                # config state colors
                if key.buttonColor is not None:
                    button.setColor('default', key.buttonColor)

                if key.hoverColor is not None:
                    button.setColor('hover', key.hoverColor)

                # config button shape, the bottom left and bottom right button
                # should have round corner to conform the overall window shape
                if row is keys[-1]:
                    if key == row[0]:
                        button.setShape(CalculatorKeyboardButton.ROUNDED_CORNER_BOTTOM_LEFT)
                    elif key == row[-1]:
                        button.setShape(CalculatorKeyboardButton.ROUNDED_CORNER_BOTTOM_RIGHT)

                # register click handle
                if key.callback is not None:
                    button.clicked.connect(key.callback)

                keyboard.addButton(button, r + 1, c + 1)

    def setProMode(self, enable):
        """
        enable/disable pro mode, switch different keyboards
        """

        if enable:
            self.proModeEnabled = True
            dm = self._runtimePro.getKeyboardDimension()

            self._runtimeBasic.reset()
            self._keyboardBasic.hide()
            self._keyboardPro.show()
        else:
            self.proModeEnabled = False
            dm = self._runtimeBasic.getKeyboardDimension()

            self._runtimePro.reset()
            self._keyboardPro.hide()
            self._keyboardBasic.show()

        # recompute window size
        width = dm[0] * dm[2] + dm[0] - 1
        height = dm[1] * dm[3] + dm[1] - 1 + 168        # 168: displayer height + displayer margin + window top space
        self.setFixedSize(width, height)

    # event handles #

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(CalculatorWindowBackboard.BRUSH_BG)
        painter.setPen(Qt.NoPen)

        path = util.createRoundRectPathUniform(QtCore.QRectF(self.rect()), config.WINDOW_ROUND_RADIUS)
        painter.drawPath(path)

        super().paintEvent(event)

    def mousePressEvent(self, event):
        # start dragging
        if event.y() <= config.WINDOW_DRAG_ZONE_HEIGHT:
            self._draggingCoord = (event.x(), event.y())
            self.isDragging = True

    def mouseReleaseEvent(self, event):
        # end dragging
        self._draggingCoord = None
        self.isDragging = False

    def mouseMoveEvent(self, event):
        # drag move window
        if self.isDragging:
            x = event.globalX() - self._draggingCoord[0]
            y = event.globalY() - self._draggingCoord[1]
            parentPt = self.mapFromParent(QtCore.QPoint(x, y))
            self.parent().move(parentPt.x(), parentPt.y())

    def _eatGlobalShortcut(self, event):
        """
        intercept global shortcut key events,
        return True/False for whether interception happened
        """

        if event.modifiers() == Qt.ControlModifier:
            key = event.key()
            if key == Qt.Key_Q:
                # Ctrl-Q quit app
                self.parent().close()
                return True
            elif key == Qt.Key_C:
                # Ctrl-C copy current content of displayer
                content = self._displayer.getPrimaryContent()
                clipboard = QtWidgets.QApplication.clipboard()
                clipboard.setText(content, QtGui.QClipboard.Clipboard)
                return True
            else:
                return False
        else:
            return False

    def eventFilter(self, qObject, event):
        """
        global event filter, intercepts global shortcut and keyboard input events
        """

        if event.type() == QEvent.KeyPress:
            if not self._eatGlobalShortcut(event):
                # if global shortcut is not intercepted, use keyboard event handle
                # of current actived keyboard
                if self.proModeEnabled:
                    self._runtimePro.onKeyboardEvent(event)
                else:
                    self._runtimeBasic.onKeyboardEvent(event)

            return True
        else:
            return False

    @pyqtSlot(CalculatorRuntime)
    def onRuntimeModelChange(self, runtime):
        """
        runtime model change slot, update displayer content
        """

        model = runtime.model
        self._displayer.setPrimaryContent(model.input, runtime.justEvaluated())
        self._displayer.setSecondaryContent(model.hint)

class CalculatorWindow(QtWidgets.QWidget):
    """
    main window of the app
    """

    def __init__(self):
        super().__init__(parent=None)

        # initiate window attributes
        self._initWindow()

        # backboard widget
        self._backboardMargin = config.WINDOW_DROPSHADOW_RADIUS + 2
        self._backboard = self._addBackboard()

        # topbar widgets
        self._windowLabel = self._addWindowLabel()
        self._topButtons = self._addTopButtons()

        # switch to basic mode by default
        self._backboard.setProMode(False)
        self._updateGlobalLayout()

        # compute united bounding box of all screens for further auto window position adjustment
        self._screenRect = util.getAllScreenRect()

    def _initWindow(self):
        self.setWindowTitle("Calculator")

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowOpacity(config.WINDOW_OPACITY)

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

    def _addBackboard(self):
        backboard = CalculatorWindowBackboard(parent=self)
        backboard.move(self._backboardMargin, self._backboardMargin)
        return backboard

    def _addWindowLabel(self):
        """
        the visual window title
        """

        label = QtWidgets.QLabel(self.windowTitle(), parent=self)
        label.setObjectName("CalculatorWindowTitle")
        label.move(self._backboardMargin + 15, self._backboardMargin + 12)
        label.setAttribute(Qt.WA_TransparentForMouseEvents)

        return label

    def _addTopButtons(self):
        """
        create topbar buttons, return array of the created button in visual order
        """

        # close button
        closeBtn = WindowButton('close', parent=self)
        closeBtn.configForegroundColors({
            QtWidgets.QStyle.State_None: config.WINDOW_TOOL_BTN_FG,
            QtWidgets.QStyle.State_MouseOver: config.WINDOW_TOOL_BTN_FG_ACTIVE
        })
        closeBtn.configBackgroundColors({
            QtWidgets.QStyle.State_None: config.WINDOW_TOOL_BTN_BG,
            QtWidgets.QStyle.State_MouseOver: config.WINDOW_TOOL_BTN_CLOSE_BG_HOVER
        })

        closeBtn.setObjectName("CalculatorCloseBtn")
        closeBtn.clicked.connect(self.close)

        # pin button
        pinBtn = WindowButton('tack-pin', parent=self)
        pinBtn.configForegroundColors({
            QtWidgets.QStyle.State_None: config.WINDOW_TOOL_BTN_FG,
            QtWidgets.QStyle.State_On: config.WINDOW_TOOL_BTN_FG_ACTIVE
        })
        pinBtn.configBackgroundColors({
            QtWidgets.QStyle.State_None: config.WINDOW_TOOL_BTN_BG,
            QtWidgets.QStyle.State_MouseOver: config.WINDOW_TOOL_BTN_PIN_BG_HOVER,
            QtWidgets.QStyle.State_On: config.WINDOW_TOOL_BTN_PIN_BG_CHECKED
        })

        pinBtn.setObjectName("CalculatorPinBtn")
        pinBtn.setCheckable(True)
        pinBtn.toggled.connect(self._togglePinBtn)

        # pro mode button
        proBtn = WindowButton('calculations', parent=self)
        proBtn.configForegroundColors({
            QtWidgets.QStyle.State_None: config.WINDOW_TOOL_BTN_FG,
            QtWidgets.QStyle.State_On: config.WINDOW_TOOL_BTN_FG_ACTIVE
        })
        proBtn.configBackgroundColors({
            QtWidgets.QStyle.State_None: config.WINDOW_TOOL_BTN_BG,
            QtWidgets.QStyle.State_MouseOver: config.WINDOW_TOOL_BTN_PRO_BG_HOVER,
            QtWidgets.QStyle.State_On: config.WINDOW_TOOL_BTN_PRO_BG_CHECKED
        })

        proBtn.setObjectName("CalculatorProModeBtn")
        proBtn.setCheckable(True)
        proBtn.toggled.connect(self._toggleProBtn)

        return [proBtn, pinBtn, closeBtn]

    def _updateGlobalLayout(self):
        """
        update window size and toolbar button position due to backboard change
        """

        backboardRect = self._backboard.rect()
        borderOffset = self._backboardMargin * 2
        width = backboardRect.width() + borderOffset
        height = backboardRect.height() + borderOffset
        self.setFixedSize(width, height)

        x = width - self._backboardMargin -10
        y = self._backboardMargin + 10
        for i in reversed(range(len(self._topButtons))):
            btn = self._topButtons[i]
            x -= btn.width()
            btn.move(x, y)
            x -= 10

    # topbar button handles #

    @pyqtSlot(bool)
    def _togglePinBtn(self, isChecked):
        # pin window on top of the window stack
        if isChecked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)

        # the window may be recreated on some platform, call `show()` force the window to display
        self.show()

        # ensure window focus
        self._backboard.setFocus()

    def _adjustWindowPos(self):
        """
        adjust window position, prevent the window from moving out of the visual area
        """

        screenRect = self._screenRect
        windowRect = self.geometry()

        offset = [0, 0]

        if windowRect.x() < screenRect.x():
            offset[0] = screenRect.x() - windowRect.x()
        else:
            windowXRange = windowRect.x() + windowRect.width()
            if windowXRange > screenRect.width():
                offset[0] = screenRect.width() - windowXRange

        if windowRect.y() < screenRect.y():
            offset[1] = screenRect.y() - windowRect.y()
        else:
            windowYRange = windowRect.y() + windowRect.height()
            if windowYRange > screenRect.height():
                offset[1] = screenRect.height() - windowYRange

        self.move(windowRect.x() + offset[0], windowRect.y() + offset[1])

    @pyqtSlot(bool)
    def _toggleProBtn(self, isChecked):
        # enable/disable pro mode
        self._backboard.setProMode(isChecked)
        self._updateGlobalLayout()
        self._adjustWindowPos()

        # ensure window focus
        self._backboard.setFocus()
