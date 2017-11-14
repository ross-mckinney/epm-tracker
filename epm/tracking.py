# Tracking Dialog/widgets go here.
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from _tracking import (
    calc_background_image,
    threshold_image
)

class TrackingSettings:
    """
    Parameters
    ----------
    threshold : int, optional
        Threshold for detecting mouse after background subtraction.

    background_n_frames : int, optional (default=200)
        How many frames to use to calculate background image.

    exclusion_mask : np.array, optional
        Which region of the image should NOT be included in tracking.

    exclusion_mask_filename : string, optional
        File that contains information about exclusion_mask.

    save_filename : string, optional
        Where to save
    """
    def __init__(self, threshold=None, background_n_frames=200, exclusion_mask=None,
        exculsion_mask_filename=None, save_filename=None):
        self.threshold = threshold
        self.background_n_frames = background_n_frames
        self.exclusion_mask = exclusion_mask
        self.exclusion_mask_filename = exculsion_mask_filename
        self.save_filename = save_filename

class ThresholdWidget(QWidget):
    def __init__(self, video, parent=None):
        super(ThresholdWidget, self).__init__(parent)
        self.video = video

        self.tracking_setting = TrackingSettings()

        self.setup_image_groupbox_ui()
        self.setup_input_groupbox_ui()

        layout = QVBoxLayout()

    def setup_image_groupbox_ui(self):
        self.image_groupbox = QGroupBox()

        layout = QHBoxLayout()

        self.raw_image, _ = self.video.get_frame(0)
        self.background_image = calc_background_image(
            self.video, self.tracking_settings.background_n_frames)
        self.thresholded_image = threshold_image(self.raw_image,
            self.background_image, self.tracking_settings.threshold)

    def setup_input_groupbox_ui(self):
        pass

class TrackingDialog(QDialog):
    def __init__(self, video, parent=None):
        super(TrackingDialog, self).__init__(parent)
        self.video = video
        self.tracking_settings = TrackingSettings()
        self.setup_ui()

    def setup_ui(self):
        pass
