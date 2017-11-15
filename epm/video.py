
import time

import motmot.FlyMovieFormat.FlyMovieFormat as FMF
import numpy as np
from skimage.draw import line_aa, polygon_perimeter, circle
from skimage.color import gray2rgb
from skimage.util import (
    img_as_ubyte, # np.uint8
    img_as_float  # np.float
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from _tracking import (
    convert_img_to_float,
    convert_img_to_uint8
)
from utils import get_q_image, get_mouse_coords

class VideoWidget(QWidget):
    """Simple widget to display video data.

    This is just a QLabel which displays and
    allows users to navigate between frames in a video.

    Attributes
    ----------
    video : motmot.FlyMovieFormat.FlyMovie
        Video to display in widget.

    is_playing : bool (default = False)
        Whether or not the video is playing.

    current_frame_ix : int
        Frame index of currently-displayed image in label.

    frame_rate : int (default = 24)
        How fast the video should be playing (in frames per second).

    frame_label : QLabel
        QLabel that will display the video data.

    video_filename : string
        Path to video file currently being displayed.

    tracking_data : pd.DataFrame
        DataFrame containing tracking data associated with the current video.

    Signals
    -------
    frame_changed : int, str, int
        Signal holding the following values:

        1. frame number : int
            Current frame number being displayed.

        2. time : str
            Formatted as HH:MM:SS, based on the mean frame rate calculated
            upon loading video.

        3. frame rate : int
            Mean frame rate of video (rounded to floor).
    """

    frame_changed = pyqtSignal(int, str, int)

    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)

        self.video = None
        self.video_filename = None
        self.tracking_data = None
        self.is_playing = False
        self.current_frame_ix = 0
        self.frame_rate = 30

        self.frame_label = QLabel()
        # this allows the image to stretch when the window is resized
        self.frame_label.setScaledContents(True)


        # set the frame_label to a blank image that is the same size/shape
        # as our video data
        img = np.zeros(shape=(240, 320), dtype=np.uint8)
        pixmap = QPixmap.fromImage(get_q_image(img))
        self.frame_label.setPixmap(pixmap)

        # set the layout of this widget to a single QLabel
        layout = QGridLayout()
        layout.addWidget(self.frame_label, 0, 0)
        self.setLayout(layout)

    def _frame_to_time(self, ix):
        """Converts a given frame to a formatted time string (HH:MM:SS)"""
        total_seconds = int(ix) / int(self.frame_rate)
        hours = total_seconds / 3600
        minutes = (total_seconds - (hours * 3600)) / 60
        seconds = (total_seconds - (minutes * 60) - (hours * 3600))
        return '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds)

    def set_video(self, video_filename):
        self.video_filename = video_filename
        self.video = FMF.FlyMovie(video_filename)
        self.update_frame_label(0)

    def previous_frame(self):
        self.update_frame_label(self.current_frame_ix - 1)

    def next_frame(self):
        self.update_frame_label(self.current_frame_ix + 1)

    def play(self):
        self.is_playing = True

        while self.is_playing:
            start_time = time.time()

            self.next_frame()
            QApplication.processEvents()

            end_time = time.time()
            elapsed_time = end_time - start_time
            if (1. / self.frame_rate - elapsed_time) > 0:
                time.sleep(1. / self.frame_rate - elapsed_time)

    def pause(self):
        self.is_playing = False

    @pyqtSlot(int)
    def update_frame_label(self, frame_number=None):
        if frame_number is None:
            frame_number = self.current_frame_ix

        if frame_number < 0:
            self.current_frame_ix = 0
        elif frame_number >= self.video.get_n_frames():
            self.current_frame_ix = self.video.get_n_frames() - 1
        else:
            self.current_frame_ix = frame_number

        img, _ = self.video.get_frame(self.current_frame_ix)

        # annotate the image if we have tracking_data available.
        if self.tracking_data is not None:
            img = img_as_float(img)
            img = gray2rgb(img)
            centroid_rr = self.tracking_data['rr'][self.current_frame_ix]
            centroid_cc = self.tracking_data['cc'][self.current_frame_ix]
            rr, cc = circle(centroid_rr, centroid_cc, 3)
            img[rr, cc, :] = [1., 0, 0]
            img = img_as_ubyte(img)

        pixmap = QPixmap.fromImage(get_q_image(img))
        self.frame_label.setPixmap(pixmap)
        self.frame_changed.emit(
            self.current_frame_ix,
            self._frame_to_time(self.current_frame_ix),
            int(self.frame_rate)
            )
