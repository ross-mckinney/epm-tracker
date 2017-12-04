# Widgets associated with setting image pixel thresholds.

import os
import sys

from time import gmtime, strftime

import numpy as np
import pandas as pd
from skimage.draw import polygon

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from _tracking_algorithms import (
    get_otsu_threshold,
    calc_background_image,
    convert_img_to_uint8,
    threshold_image
)
from _utils import get_q_image


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

        layout.addWidget(self.image_groupbox, 0, 0, 1, 3)
        layout.addWidget(self.input_groupbox, 1, 0, 1, 1)
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

        layout = QHBoxLayout()

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
