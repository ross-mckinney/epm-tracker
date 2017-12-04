# Tracking objects, associated with GUI go here.

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from _tracking_algorithms import (
    calc_background_image,
    threshold_image,
    get_otsu_threshold,
    convert_img_to_uint8,
    find_mouse
)


class Tracker(QObject):
    """Class used to track mouse in EPM.

    Parameters
    ----------
    video : motmot.FlyMovieFormat.FlyMovieFormat
        Video to track.

    tracking_settings : TrackingSettings
        Tracking settings used to track video.

    Signals
    -------
    progress : pyqtSignal
        Frame number currently being tracked. Emitted in call to
        track_video().
    """

    progress = pyqtSignal(int)

    def __init__(self, video, tracking_settings, parent=None):
        super(Tracker, self).__init__(parent)
        self.video = video
        self.tracking_settings = tracking_settings

    def track_video(self):
        b_img = calc_background_image(
            self.video,
            n_frames=self.tracking_settings.background_n_frames)

        props = []
        for ix in xrange(self.video.get_n_frames()):
            img, _ = self.video.get_frame(ix)
            props.append(
                find_mouse(img, b_img,
                    threshold=self.tracking_settings.threshold,
                    inclusion_mask=self.tracking_settings.inclusion_mask)
                )
            self.progress.emit(ix)

        return props
