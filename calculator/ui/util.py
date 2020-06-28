import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets


def createRoundRectPath(rectF: QtCore.QRectF, r1: float, r2: float, r3: float, r4: float) -> QtGui.QPainterPath:
    """
    create a rounded rectangle painter path

    :param r1: top left radius
    :param r2: top right radius
    :param r3: bottom right radius
    :param r4: bottom left radius
    """

    r1 *= 2
    r2 *= 2
    r3 *= 2
    r4 *= 2

    path = QtGui.QPainterPath()

    width = rectF.width()
    height = rectF.height()
    x = rectF.x()
    y = rectF.y()

    path.moveTo(x + width - r2, y)
    path.lineTo(x + r1, y)
    path.arcTo(x, y, r1, r1, 90.0, 90.0)
    path.lineTo(x, y + height - r4)
    path.arcTo(x, y + height - r4, r4, r4, 180.0, 90.0)
    path.lineTo(x + width - r3, y + height)
    path.arcTo(x + width - r3, y + height - r3, r3, r3, 270.0, 90.0)
    path.lineTo(x + width, y + r2)
    path.arcTo(x + width - r2, y, r2, r2, 0.0, 90.0)

    path.closeSubpath()

    return path

def createRoundRectPathUniform(rectF: QtCore.QRectF, radius: float) -> QtGui.QPainterPath:
    """
    create a painter path of a rounded rectangle of which all corners have the same radius
    """

    path = QtGui.QPainterPath()
    path.addRoundedRect(rectF, radius, radius)
    return path

def getAllScreenRect() -> QtCore.QRect:
    """
    get the united bounding box of all screens
    """

    rect = QtCore.QRect(0, 0, 0, 0)
    for screen in QtWidgets.QApplication.screens():
        rect = rect.united(screen.availableGeometry())

    return rect