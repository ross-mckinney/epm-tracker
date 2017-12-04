
from PyQt4.QtCore import *
from PyQt4.QtGui import *

def get_q_image(image):
    """Converts a numpy array to a QImage.

    Parameters
    ----------
    image : 2D or 3D np.ndarray
        Numpy array to convert to a QImage.

    Returns
    -------
    qimage : 2D or 3D QImage
        QImage object conatining the specified numpy array.
    """
    if len(image.shape) == 3:
        rgb = True
    elif len(image.shape) == 2:
        rgb = False

    height, width = image.shape[:2]

    if not rgb:
        try:
            return QImage(image.tostring(), width, height, QImage.Format_Indexed8)
        except:
            return QImage(image.data, width, height, QImage.Format_Indexed8)
    else:
        try:
            return QImage(image.data, width, height, QImage.Format_RGB888)
        except:
            return QImage(image.tostring(), width, height, QImage.Format_RGB888)

def get_mouse_coords(event):
    cc = event.pos().x()
    rr = event.pos().y()
    return rr, cc
