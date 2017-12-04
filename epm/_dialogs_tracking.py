#

import os
import sys

from time import gmtime, strftime

import numpy as np
import pandas as pd

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from widgets import (
    MaskWidget,
    ThresholdWidget,
)
from _tracking_settings import TrackingSettings
from _tracking_qobjects import Tracker


class TrackingDialog(QDialog):

    tracking_complete = pyqtSignal(bool, str)

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

        self.mask_widget = MaskWidget(self.video, self.tracking_settings)

        self.stacked_widget.addWidget(self.mask_widget)
        self.stacked_widget.addWidget(self.threshold_widget)

        self.next_button = QPushButton('>>')
        self.next_button.clicked.connect(self.next_stacked_widget)
        self.previous_button = QPushButton('<<')
        self.previous_button.clicked.connect(self.previous_stacked_widget)
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
        self.stacked_widget_page_label = QLabel(
            'Page: 1/2')

        self.status_bar.addPermanentWidget(self.progress_bar)
        self.status_bar.addWidget(self.stacked_widget_page_label)

    @pyqtSlot()
    def next_stacked_widget(self):
        self.stacked_widget_page = self.stacked_widget.currentIndex()
        n_widgets_in_stack = self.stacked_widget.count()
        if self.stacked_widget_page + 1 < n_widgets_in_stack:
            self.stacked_widget_page += 1
        self.stacked_widget.setCurrentIndex(self.stacked_widget_page)
        self.stacked_widget_page_label.setText(
            'Page: {}/{}'.format(self.stacked_widget_page + 1,
            n_widgets_in_stack))

    @pyqtSlot()
    def previous_stacked_widget(self):
        self.stacked_widget_page = self.stacked_widget.currentIndex()
        if self.stacked_widget_page > 0:
            self.stacked_widget_page -= 1
        self.stacked_widget.setCurrentIndex(self.stacked_widget_page)
        self.stacked_widget_page_label.setText(
            'Page: {}/{}'.format(self.stacked_widget_page + 1,
            self.stacked_widget.count()))

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
            savename = self.tracking_settings.save_filename
            if savename.split('.')[-1] != 'xlsx':
                savename += '.xlsx'
        else:
            savename = os.path.join(
                os.path.expanduser('~'),
                strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())
                )
            savename += '.xlsx'

        tracking_data.to_excel(
            savename,
            na_rep='NA',
            index_label='frame',
            sheet_name='RawData')

        self.tracking_complete.emit(True, savename)
        self.close()
