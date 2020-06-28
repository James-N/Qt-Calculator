import json
import os
import os.path

import PyQt5.QtGui as QtGui


FONT_EXTS = ['.ttf', '.otf', '.oet']


gIconFontCharMap = {}

def loadIconFont(fontFile: str, charMapFile: str):
    """
    load icon font into current application
    """

    id_ = QtGui.QFontDatabase.addApplicationFont(fontFile)
    if id_ >= 0:
        with open(charMapFile, 'r', encoding='utf-8') as inf:
            charMap = json.load(inf)
            if charMap is not None and isinstance(charMap, dict):
                global gIconFontCharMap
                gIconFontCharMap = charMap

def getIconCode(iconName: str) -> str:
    """
    get code of the given icon
    """

    code = gIconFontCharMap.get(iconName, None)
    if code is not None:
        return chr(int(code, 16))
    else:
        return ''

def getIconFont() -> QtGui.QFont:
    """
    get QFont object of global icon font
    """

    font = QtGui.QFont('IcoFont')
    font.setPixelSize(32)
    return font

def loadFontFamily(fontDir: str):
    """
    scan the given directory, load all the font files into current application
    """

    with os.scandir(fontDir) as it:
        for entry in it:
            if entry.is_file():
                fpath = entry.path
                if os.path.splitext(fpath)[1].lower() in FONT_EXTS:
                    QtGui.QFontDatabase.addApplicationFont(fpath)
