import os.path

dirname = os.path.dirname(__file__)
resourceDir = os.path.join(dirname, 'resource')


def getResourcePath(name: str) -> str:
    """
    get full path of resource files under resource directory
    """

    return os.path.join(resourceDir, name)