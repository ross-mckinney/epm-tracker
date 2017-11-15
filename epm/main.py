
import os, sys

import motmot.FlyMovieFormat.FlyMovieFormat as FMF
import numpy as np
import pandas as pd
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import qdarkstyle

from video import VideoWidget
from tracking import TrackingDialog

DIR = os.path.dirname(__file__)
DEBUG = False

class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.root_folder = os.path.expanduser("~")

        self.video_widget = VideoWidget()
        self.setCentralWidget(self.video_widget)

        #create menus
        self.file_menu = self.menuBar().addMenu('&File')
        self.video_menu = self.menuBar().addMenu('Video')
        self.tracking_menu = self.menuBar().addMenu('Tracking')

        #create toolbar for navigating through videos
        self.video_toolbar = self.addToolBar('Video')
        self.video_trackbar = self.addToolBar('Video Track Bar')

        self.set_file_menu()
        self.set_video_menu()
        self.set_tracking_menu()

        self.set_slider()
        self.set_status()
        self.update_status(0, 'NA:NA:NA', -1)

        if DEBUG:
            base_dir = '/home/ben-shahar/Dropbox/ben-shahar_lab/collaborations/anna'
            video_filename = os.path.join(base_dir, 'test2.fmf')
            tracking_data_filename = os.path.join('/home/ben-shahar/',
                'Wed, 15 Nov 2017 18:34:22 +0000.xlsx')
            assert os.path.isfile(video_filename), 'video not found'
            assert os.path.isfile(tracking_data_filename), 'tracking data not found'

            self.open_video(video_filename)
            tracking_data = pd.read_excel(tracking_data_filename, index='frame')
            self.video_widget.tracking_data = tracking_data
            self.video_widget.update_frame_label()

    def add_menu_action(self, menu, name, connection, status_tip,
        shortcut=None, icon=None, tool_bar=None, return_action=False):
        """Helper function for adding a QAction to a menu.

        Parameters
        ----------
        menu : QMenu
            Which menu to add new QAction to.

        name : string
            Name of new QAction. This is displayed as the QAction
            text in the QMenu.

        connection : function
            Which function should the QAction be connected to.

        status_tip : string
            Status tip to display on MouseOver.

        shortcut : QKeySequence or None (default = None)
            Shortcut to execute action.

        icon : QIcon or None (default = None)
            Icon to attach to QAction.

        tool_bar : QToolBar or None
            QToolBar to attach QAction to (in addition to the specified QMenu).

        return_action : bool (default = False)
            Whether or not to return the action.
        """
        if icon is None:
            action = QAction(name, self)
        else:
            action = QAction(icon, name, self)

        if shortcut is not None:
            action.setShortcut(shortcut)

        action.setStatusTip(status_tip)
        action.triggered.connect(connection)
        menu.addAction(action)

        if tool_bar is not None:
            tool_bar.addAction(action)

        if return_action:
            return action

    def set_file_menu(self):
        self.add_menu_action(
            menu=self.file_menu,
            name='Open Video',
            connection=self.open_video,
            status_tip='Open an individual video.',
            shortcut=QKeySequence.Open
            )

    def set_video_menu(self):
        self.previous_action = self.add_menu_action(
            menu=self.video_menu,
            name='Previous Frame',
            connection=self.video_widget.previous_frame,
            status_tip='Go to previous frame.',
            icon=QIcon(os.path.join(DIR, 'icons', 'prev_icon.png')),
            tool_bar=self.video_toolbar,
            return_action=True
            )
        self.previous_action.setEnabled(False)
        self.previous_action.setShortcut(QKeySequence(','))

        self.play_action = self.add_menu_action(
            menu=self.video_menu,
            name='Play',
            connection=self.video_widget.play,
            status_tip='Play Video.',
            icon=QIcon(os.path.join(DIR, 'icons', 'play_icon.png')),
            tool_bar=self.video_toolbar,
            return_action=True
            )
        self.play_action.setEnabled(False)
        self.play_action.setShortcut(QKeySequence(']'))

        self.stop_action = self.add_menu_action(
            menu=self.video_menu,
            name='Stop',
            connection=self.video_widget.pause,
            status_tip='Stop Video.',
            icon=QIcon(os.path.join(DIR, 'icons', 'stop_icon.png')),
            tool_bar=self.video_toolbar,
            return_action=True
            )
        self.stop_action.setEnabled(False)
        self.stop_action.setShortcut(QKeySequence('['))

        self.next_action = self.add_menu_action(
            menu=self.video_menu,
            name='Next Frame',
            connection=self.video_widget.next_frame,
            status_tip='Go to next frame.',
            icon=QIcon(os.path.join(DIR, 'icons', 'next_icon.png')),
            tool_bar=self.video_toolbar,
            return_action=True
            )
        self.next_action.setEnabled(False)
        self.next_action.setShortcut(QKeySequence('.'))

        self.stop_start_action = self.add_menu_action(
            menu=self.video_menu,
            name='Pause/Play',
            connection=self.stop_start,
            status_tip='Start playing, pause, or resume playing video.',
            return_action=True
            )
        self.stop_start_action.setEnabled(False)
        self.stop_start_action.setShortcut(QKeySequence(Qt.Key_Space))

    def set_tracking_menu(self):
        self.tracking_action = self.add_menu_action(
            menu=self.tracking_menu,
            name='Track Video',
            connection=self.track_video,
            status_tip='Track current video.',
            return_action=True
        )
        self.tracking_action.setEnabled(False)

    def open_video(self, video_filename=None):
        if self.video_widget.video is not None:
            self.video_widget.video = None
            self.video_widget.tracking_data = None
            self.video_widget.is_playing = False
            self.video_widget.video_filename = None

        if not isinstance(video_filename, str):
            file_dialog = QFileDialog(self)
            video_filename = str(file_dialog.getOpenFileName(
                caption='Open Video File',
                filter='Video Files (*.fmf)',
                directory=self.root_folder
                ))

        if not os.path.isfile(video_filename):
            return

        self.video_widget.set_video(video_filename)
        self.video_info_label.setText(
            'Current Video: {}'.format(
                os.path.basename(video_filename)
            ))
        self.frame_info_label.setText(
            'Frame: 0 (00:00:00) | FPS: -1'
        )
        self.slider.setMaximum(self.video_widget.video.get_n_frames() - 1)
        self.enable_video_controls(True)

    def enable_video_controls(self, flag=True):
        #connect video_player signals
        if flag is True:
            self.video_widget.frame_changed.connect(self.update_status)

        #enable video controls
        self.previous_action.setEnabled(flag)
        self.next_action.setEnabled(flag)
        self.play_action.setEnabled(flag)
        self.stop_action.setEnabled(flag)
        self.stop_start_action.setEnabled(flag)
        self.tracking_action.setEnabled(flag)

        self.slider.setEnabled(flag)

    def set_slider(self):
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.video_trackbar.addWidget(self.slider)
        self.slider.valueChanged.connect(self.video_widget.update_frame_label)
        self.video_widget.frame_changed.connect(self.update_slider)
        self.slider.setEnabled(False)

    def set_status(self):
        status = self.statusBar()
        self.frame_info_label = QLabel()
        self.frame_info_label.setFrameStyle(
            QFrame.StyledPanel | QFrame.Sunken)
        self.frame_info_label.setText('Frame: NA (00:00:00)')

        self.video_info_label = QLabel()
        self.video_info_label.setText('Current Video: NA')

        status.addPermanentWidget(self.frame_info_label)
        status.addWidget(self.video_info_label)

    def track_video(self):
        dialog = TrackingDialog(self.video_widget.video)
        dialog.tracking_complete.connect(self.load_tracking_data)
        dialog.exec_()

    @pyqtSlot(bool, str)
    def load_tracking_data(self, is_complete, tracking_data_filename):
        if not is_complete:
            return

        tracking_data_filename = str(tracking_data_filename)
        try:
            tracking_data = pd.read_excel(tracking_data_filename, index='frame')
            self.video_widget.tracking_data = tracking_data
            self.video_widget.update_frame_label()
        except:
            print 'Could not load trackind_data_filename: {}'.format(tracking_data_filename)

    @pyqtSlot(int, str, int)
    def update_status(self, ix, hmms, frame_rate):
        self.frame_info_label.setText(
            'Frame: {} ({}) | FPS: {}'.format(ix, hmms, frame_rate)
        )

    @pyqtSlot(int)
    def update_slider(self, ix):
        self.slider.setValue(ix)

    @pyqtSlot()
    def stop_start(self):
        if self.video_widget.is_playing:
            self.video_widget.pause()
        else:
            self.video_widget.play()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(pyside=False))

    main_window = MainWindow()
    main_window.setWindowTitle('EPM Tracker')

    main_window.show()
    main_window.resize(320*3, 240*3)
    app.exec_()

if __name__ == '__main__':
    main()
