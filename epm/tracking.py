# Tracking Dialog/widgets go here.
import os
from time import gmtime, strftime

import numpy as np
import pandas as pd

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from _tracking import (
    calc_background_image,
    threshold_image,
    get_otsu_threshold,
    convert_img_to_uint8,
    find_mouse
)
import _tracking

from utils import (
    get_q_image,
    get_mouse_coords
)

class Tracker(QObject):
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
                find_mouse(img, b_img, threshold=self.tracking_settings.threshold)
                )
            self.progress.emit(ix)

        return props

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
    def __init__(self, video, tracking_settings, parent=None):
        super(ThresholdWidget, self).__init__(parent)
        self.video = video
        self.frame_number = 0

        self.tracking_settings = tracking_settings

        self.setup_image_groupbox_ui()
        self.setup_input_groupbox_ui()
        self.setup_frame_number_groupbox_ui()
        # self.setup_track_button_groupbox_ui()

        layout = QGridLayout()

        layout.addWidget(self.image_groupbox, 0, 0, 3, 1)
        layout.addWidget(self.input_groupbox, 0, 1, 1, 1)
        layout.addWidget(self.frame_number_groupbox, 1, 1, 1, 1)
        # layout.addWidget(self.track_button_groupbox, 2, 1, 1, 1)
        self.setLayout(layout)

        self.tracking_settings.threshold = get_otsu_threshold(
            self.raw_image, self.background_image
        )

    def setup_image_groupbox_ui(self):
        """Setups image_groupbox with three images, which
        represent the first, raw image of the video. The calculated
        background image, and the thresholded image."""
        self.image_groupbox = QGroupBox('Images')

        layout = QVBoxLayout()

        self.raw_image, _ = self.video.get_frame(0)
        self.background_image = calc_background_image(
            self.video, self.tracking_settings.background_n_frames)
        self.thresholded_image = convert_img_to_uint8(
            threshold_image(self.raw_image,
                self.background_image, self.tracking_settings.threshold)
            )

        self.raw_image_label = QLabel()
        self.background_image_label = QLabel()
        self.threshold_image_label = QLabel()

        raw_image_pixmap = QPixmap.fromImage(get_q_image(self.raw_image))
        background_image_pixmap = QPixmap.fromImage(
            get_q_image(self.background_image))
        threshold_image_pixmap = QPixmap.fromImage(
            get_q_image(self.thresholded_image))

        self.raw_image_label.setPixmap(raw_image_pixmap)
        self.background_image_label.setPixmap(background_image_pixmap)
        self.threshold_image_label.setPixmap(threshold_image_pixmap)

        layout.addWidget(self.background_image_label)
        layout.addWidget(self.raw_image_label)
        layout.addWidget(self.threshold_image_label)

        self.image_groupbox.setLayout(layout)

    def setup_input_groupbox_ui(self):
        self.input_groupbox = QGroupBox('Tracking Settings')

        layout = QGridLayout()
        threshold_name_label = QLabel('Set threshold: ')
        background_n_frames_label = QLabel(
            'N of frames to calculate background: ')
        save_filename_label = QLabel('Save filename (.xlsx): ')

        layout.addWidget(threshold_name_label, 0, 0, 1, 1)
        layout.addWidget(background_n_frames_label, 1, 0, 1, 1)
        layout.addWidget(save_filename_label, 2, 0, 1, 1)

        self.threshold_spin_box = QSpinBox()
        self.threshold_spin_box.setMinimum(0)
        self.threshold_spin_box.setMaximum(100)
        self.threshold_spin_box.setValue(
            get_otsu_threshold(self.raw_image, self.background_image) * 100
        )
        self.threshold_spin_box.valueChanged.connect(
            self.update_threshold_image)

        self.background_frames_spinbox = QSpinBox()
        self.background_frames_spinbox.setMinimum(0)
        self.background_frames_spinbox.setMaximum(
            self.video.get_n_frames()
        )
        self.background_frames_spinbox.setValue(
            self.tracking_settings.background_n_frames
        )
        self.background_frames_spinbox.valueChanged.connect(
            self.update_background_image)

        self.save_filename_lineedit = QLineEdit()
        self.save_filename_lineedit.setText('Save name (.xlsx)')
        self.save_filename_lineedit.setReadOnly(True)
        self.save_filename_browse_button = QPushButton('Browse')
        self.save_filename_browse_button.clicked.connect(self.set_save_file)

        layout.addWidget(self.threshold_spin_box, 0, 1, 1, 1)
        layout.addWidget(self.background_frames_spinbox, 1, 1, 1, 1)
        layout.addWidget(self.save_filename_lineedit, 2, 1, 1, 2)
        layout.addWidget(self.save_filename_browse_button, 2, 3, 1, 1)

        self.input_groupbox.setLayout(layout)

    def setup_frame_number_groupbox_ui(self):
        self.frame_number_groupbox = QGroupBox('Jump to Frame')

        layout = QGridLayout()

        self.frame_number_slider = QSlider(Qt.Horizontal)
        self.frame_number_slider.setMaximum(self.video.get_n_frames() - 1)
        self.frame_number_slider.valueChanged.connect(
            self.update_images)

        self.frame_number_spinbox = QSpinBox()
        self.frame_number_spinbox.setMinimum(0)
        self.frame_number_spinbox.setMaximum(self.video.get_n_frames() - 1)
        self.frame_number_spinbox.valueChanged.connect(
            self.update_images)

        self.random_frame_button = QPushButton('Random Frame')
        self.random_frame_button.clicked.connect(self.update_random_frame)

        layout.addWidget(self.frame_number_slider, 0, 0, 1, 3)
        layout.addWidget(self.frame_number_spinbox, 1, 0, 1, 1)
        layout.addWidget(self.random_frame_button, 2, 0, 1, 1)

        self.frame_number_groupbox.setLayout(layout)
    #
    # def setup_track_button_groupbox_ui(self):
    #     self.track_button_groupbox = QGroupBox('Begin Tracking')
    #     layout = QGridLayout()
    #
    #     self.track_button = QPushButton('Track')
    #     layout.addWidget(QLabel('\t'*4), 0, 0, 1, 3)
    #     layout.addWidget(QLabel('\t'*4), 1, 0, 1, 3)
    #     layout.addWidget(QLabel('\t'*4), 2, 0, 1, 3)
    #     layout.addWidget(self.track_button, 3, 3, 1, 1)
    #     self.track_button_groupbox.setLayout(layout)

    @pyqtSlot()
    def set_save_file(self):
        file_dialog = QFileDialog(self)
        tracking_savefile = str(file_dialog.getSaveFileName(
            caption='Save File',
            filter='Spreadsheet (*.xlsx)'
            ))
        if tracking_savefile != '':
            self.tracking_settings.save_filename = tracking_savefile
            self.save_filename_lineedit.setText(tracking_savefile)

    @pyqtSlot()
    def update_random_frame(self):
        random_ix = np.random.randint(0, self.video.get_n_frames())
        self.update_images(random_ix)

    @pyqtSlot(int)
    def update_images(self, frame_ix):
        self.frame_number = frame_ix

        if self.frame_number_spinbox.value() != frame_ix:
            self.frame_number_spinbox.setValue(frame_ix)

        if self.frame_number_slider.value() != frame_ix:
            self.frame_number_slider.setValue(frame_ix)

        self.update_raw_image(frame_ix)
        self.update_threshold_image(self.tracking_settings.threshold * 100)

    @pyqtSlot(int)
    def update_raw_image(self, frame_ix):
        self.raw_image, _ = self.video.get_frame(frame_ix)
        raw_image_pixmap = QPixmap.fromImage(get_q_image(self.raw_image))
        self.raw_image_label.setPixmap(raw_image_pixmap)

    @pyqtSlot(int)
    def update_background_image(self, n_frames):
        self.tracking_settings.background_n_frames = n_frames
        self.background_image = calc_background_image(
            self.video, self.tracking_settings.background_n_frames)
        background_image_pixmap = QPixmap.fromImage(
            get_q_image(self.background_image))
        self.background_image_label.setPixmap(background_image_pixmap)

    @pyqtSlot(int)
    def update_threshold_image(self, threshold):
        self.tracking_settings.threshold = threshold / 100.
        self.thresholded_image = convert_img_to_uint8(
            threshold_image(self.raw_image,
                self.background_image, self.tracking_settings.threshold)
            )
        threshold_image_pixmap = QPixmap.fromImage(
            get_q_image(self.thresholded_image))
        self.threshold_image_label.setPixmap(threshold_image_pixmap)

class TrackingDialog(QDialog):
    def __init__(self, video, parent=None):
        super(TrackingDialog, self).__init__(parent)
        self.video = video
        self.total_video_frames = video.get_n_frames()
        self.tracking_settings = TrackingSettings()

        self.video_tracker = Tracker(self.video, self.tracking_settings)
        self.video_tracker.progress.connect(self.update_progress_bar)

        self.setup_status_bar_ui()
        self.setup_ui()
        self.setWindowTitle('Tracking')

    def setup_ui(self):
        layout = QGridLayout()

        self.stacked_widget = QStackedWidget()
        self.threshold_widget = ThresholdWidget(
            self.video, self.tracking_settings)
        self.stacked_widget.addWidget(self.threshold_widget)

        self.next_button = QPushButton('>>')
        self.previous_button = QPushButton('<<')
        self.track_button = QPushButton('Begin Tracking')
        self.track_button.clicked.connect(self.track_video)

        layout.addWidget(self.stacked_widget, 0, 0, 4, 6)
        layout.addWidget(self.previous_button, 4, 0, 1, 1)
        layout.addWidget(self.next_button, 4, 1, 1, 1)
        layout.addWidget(self.track_button, 4, 2, 1, 1)
        layout.addWidget(self.status_bar, 5, 0, 1, 6)

        self.setLayout(layout)

    def setup_status_bar_ui(self):
        self.status_bar = QStatusBar()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(self.video.get_n_frames() - 1)

        self.stacked_widget_page = 1
        self.stacked_widget_page_label = QLabel('Page: 1/3')

        self.status_bar.addPermanentWidget(self.progress_bar)
        self.status_bar.addWidget(self.stacked_widget_page_label)

    @pyqtSlot(int)
    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress)
        QApplication.processEvents()

    @pyqtSlot()
    def track_video(self):
        self.props = self.video_tracker.track_video()

        tracking_data = pd.DataFrame()
        rr, cc = [], []
        maj, minor, area = [], [], []

        for prop in self.props:
            if prop == -1:
                rr.append(np.nan)
                cc.append(np.nan)
                maj.append(np.nan)
                minor.append(np.nan)
                area.append(np.nan)
                continue

            rr_, cc_ = prop.centroid
            rr.append(rr_)
            cc.append(cc_)
            maj.append(prop.major_axis_length)
            minor.append(prop.minor_axis_length)
            area.append(prop.area)

        tracking_data['rr'] = rr
        tracking_data['cc'] = cc
        tracking_data['area'] = area
        tracking_data['maj'] = maj
        tracking_data['min'] = minor

        if self.tracking_settings.save_filename is not None:
            tracking_data.to_excel(
                self.tracking_settings.save_filename,
                na_rep='NA',
                index_label='frame',
                sheet_name='RawData')
        else:
            savename = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
            savename += '.xlsx'
            tracking_data.to_excel(
                os.path.join(os.path.expanduser("~"), savename),
                na_rep='NA',
                index_label='frame',
                sheet_name='RawData')
