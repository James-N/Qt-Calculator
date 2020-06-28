import sys
import os.path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

import calculator.ui.uiresource as uiresource
import calculator.ui.font as font
from calculator.ui.main_window import CalculatorWindow


def run():
    app = QApplication(sys.argv)

    # load global stylesheet
    with open(uiresource.getResourcePath('main.qss'), 'r', encoding='utf-8') as inf:
        app.setStyleSheet(inf.read())

    # load ui font
    font.loadFontFamily(uiresource.getResourcePath('fonts/open-sans'))

    # load icon font
    font.loadIconFont(
        uiresource.getResourcePath('fonts/icofont/icofont.ttf'),
        uiresource.getResourcePath('fonts/icofont/icofont-map.json')
    )

    # set global default font
    # defaultFont = QFont("Arial")
    defaultFont = QFont("Open Sans")
    defaultFont.setStyleHint(QFont.Helvetica)
    QApplication.setFont(defaultFont)

    # create and display main window
    window = CalculatorWindow()
    window.show()

    app.exec_()


if __name__ == '__main__':
    run()