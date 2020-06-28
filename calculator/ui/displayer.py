import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt


class CalculatorDisplayer(QtWidgets.QWidget):
    """
    displayer for calaulator, consist of the main input area and formular area
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setFixedHeight(120)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(8, 0, 8, 20)
        layout.setSpacing(5)
        layout.addSpacerItem(QtWidgets.QSpacerItem(100, 45))
        self.setLayout(layout)

        # create and config secondary input
        secondaryInput = QtWidgets.QLineEdit('', parent=self)
        secondaryInput.setObjectName("Secondary")
        secondaryInput.setFixedHeight(20)
        secondaryInput.setReadOnly(True)
        secondaryInput.setFrame(False)
        secondaryInput.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # config secondary input font
        font = QtGui.QFont(secondaryInput.font())
        font.setWeight(QtGui.QFont.Thin)
        secondaryInput.setFont(font)

        self._secondaryInput = secondaryInput
        # since lineinput is used as a label, use the global event filter to prevent
        # keyboard events from being captured by these inputs
        self._secondaryInput.installEventFilter(parent)
        layout.addWidget(secondaryInput)

        # create and config primary input
        primaryInput = QtWidgets.QLineEdit('', parent=self)
        primaryInput.setObjectName("Primary")
        primaryInput.setFixedHeight(50)
        primaryInput.setReadOnly(True)
        primaryInput.setFrame(False)
        primaryInput.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # config primary input font
        primaryInput.ensurePolished()
        font = QtGui.QFont(primaryInput.font())
        font.setWeight(QtGui.QFont.Normal)
        primaryInput.setFont(font)

        # compute possible font sizes for primary input
        pixelSize = font.pixelSize()
        pixelSizeSmall = int(round(pixelSize * 0.8))                # font size used when input string is over length
        self._primaryInputFontSizes = (pixelSize, pixelSizeSmall)

        self._primaryInput = primaryInput
        self._primaryInput.installEventFilter(parent)
        layout.addWidget(primaryInput)

    def _updatePrimaryFontSize(self, content):
        """
        change main input font size based on content length
        """

        sizes = self._primaryInputFontSizes
        font = self._primaryInput.font()

        if len(content) < 14:
            # no need for further computing when content length is less than 14
            size = sizes[0]
        else:
            testFont = QtGui.QFont(font)
            testFont.setPixelSize(sizes[0])
            fontMetrics = QtGui.QFontMetrics(testFont)

            widgetRect = self._primaryInput.rect()
            fontRect = fontMetrics.boundingRect(content)

            size = sizes[1] if widgetRect.width() < fontRect.width() else sizes[0]

        if size != font.pixelSize():
            font.setPixelSize(size)
            self._primaryInput.setFont(font)

    def setPrimaryContent(self, content, focusStart=False):
        """
        update content of the main input area
        """

        self._updatePrimaryFontSize(content)
        self._primaryInput.setText(content)

        if focusStart:
            self._primaryInput.setCursorPosition(0)

    def getPrimaryContent(self):
        """
        get current of the main input area
        """

        return self._primaryInput.text()

    def setSecondaryContent(self, content):
        """
        update content of the forumlar display area
        """

        self._secondaryInput.setText(content)

    def getSecondaryContent(self):
        """
        get current of the forumlar display area
        """

        return self._secondaryInput.text()

    # event handles #

    def resizeEvent(self, event):
        # once window size is changed, font size of primary input may should be updated
        self._updatePrimaryFontSize(self._primaryInput.text())
        return super().resizeEvent(event)
