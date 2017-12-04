# Widgets associated with setting of the arena go here.

import os
import sys

from time import gmtime, strftime

import numpy as np
import pandas as pd
from skimage.draw import polygon

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from _tracking_algorithms import (
    convert_img_to_uint8
)
from _utils import get_q_image


class MaskPoint(QGraphicsItem):
    """This class represents a movable point that can be placed within
    a QGraphicsScene.

    Together with other MaskPoints, these objects are utilized to help
    the user define the corner points of the EPM.

    Parameters
    ----------
    color : QColor
        The color of the point.

    text : string, optional (default='')
        Any text associated with this point.

    ellipse_width : int
        The width of the displayed point.

    ellipse_height : int
        The height of the displayed point.

    ellipse_x : int
        The x-coordinate of this point (in pixel units).

    ellipse_y : int
        The y-coordinate of this point (in pixel units).
    """

    def __init__(self, ellipse_x, ellipse_y, ellipse_width, color,
        text='', parent=None):
        super(MaskPoint, self).__init__(parent)

        self.color = color
        self.text = text

        self.ellipse_width = self.ellipse_height = ellipse_width
        self.ellipse_x = ellipse_x
        self.ellipse_y = ellipse_y

        self.bounding_rect_x = self.ellipse_x - 0.5 * self.ellipse_width
        self.bounding_rect_y = self.ellipse_y - 0.5 * self.ellipse_width
        self.bounding_rect_width = self.ellipse_width
        self.bounding_rect_height = self.ellipse_height

        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsItem.ItemIsMovable)

    def boundingRect(self):
        return QRectF(self.bounding_rect_x, self.bounding_rect_y,
            self.bounding_rect_width, self.bounding_rect_height)

    def paint(self, painter, option, widget):
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.color)
        painter.drawEllipse(self.ellipse_x - 0.5 * self.ellipse_width,
            self.ellipse_y - 0.5 * self.ellipse_height,
            self.ellipse_width, self.ellipse_height)


class MaskWidget(QWidget):
    """Widget to manage setting of mask for EPM."""
    def __init__(self, video, tracking_settings, parent=None):
        super(MaskWidget, self).__init__(parent)
        self.video = video
        self.tracking_settings = tracking_settings

        self.set_graphics_scene_ui()
        self.set_mask_image_ui()

        layout=QGridLayout()
        layout.addWidget(self.mask_image_groupbox, 0, 0, 1, 4)
        layout.addWidget(self.graphics_scene_groupbox, 1, 0, 1, 2)
        self.setLayout(layout)

    def set_graphics_scene_ui(self):
        self.graphics_scene_groupbox = QGroupBox()
        layout = QGridLayout()

        self.graphics_scene = QGraphicsScene()
        #background image
        self.graphics_scene_pixmap = self.graphics_scene.addPixmap(
            QPixmap.fromImage(get_q_image(self.video.get_frame(0)[0]))
        )
        self.graphics_scene_view = QGraphicsView(self.graphics_scene)

        self.initial_mask_point_locations = np.array([
            [self.video.get_width()/4, 0],
            [self.video.get_width()/2, self.video.get_height()/3],
            [self.video.get_width()/4*3, 0],

            [self.video.get_width(), self.video.get_height()/4],
            [self.video.get_width()/3*2, self.video.get_height()/2],
            [self.video.get_width(), self.video.get_height()/4*3],

            [self.video.get_width()/4, self.video.get_height()],
            [self.video.get_width()/2, self.video.get_height()/3*2],
            [self.video.get_width()/4*3, self.video.get_height()],

            [0, self.video.get_height()/4],
            [self.video.get_width()/3, self.video.get_height()/2],
            [0, self.video.get_height()/4*3]
        ])
        point_colors = [Qt.blue, Qt.darkBlue, Qt.blue, Qt.green, Qt.darkGreen,
            Qt.green, Qt.cyan, Qt.darkCyan, Qt.cyan, Qt.magenta, Qt.darkMagenta,
            Qt.magenta]

        self.mask_points = [
            MaskPoint(self.initial_mask_point_locations[i, 0],
                self.initial_mask_point_locations[i, 1],
                10, point_colors[i], '') for i in xrange(len(point_colors))
        ]
        for mask_point in self.mask_points:
            self.graphics_scene.addItem(mask_point)

        self.generate_mask_button = QPushButton('Update Mask')
        self.generate_mask_button.clicked.connect(self.generate_mask)
        self.load_mask_button = QPushButton('Load Mask')
        self.load_mask_button.clicked.connect(self.load_mask)
        self.save_mask_button = QPushButton('Save Mask')
        self.save_mask_button.clicked.connect(self.save_mask)

        layout.addWidget(self.graphics_scene_view, 0, 0, 5, 5)
        layout.addWidget(self.generate_mask_button, 5, 4, 1, 1)
        layout.addWidget(self.load_mask_button, 6, 0, 1, 1)
        layout.addWidget(self.save_mask_button, 6, 1, 1, 1)

        self.graphics_scene_groupbox.setLayout(layout)

    def set_mask_image_ui(self):
        self.mask_image_groupbox = QGroupBox('EPM Arena Mask')
        layout = QHBoxLayout()

        self.arena_image, _ = self.video.get_frame(0)
        self.mask_image = np.zeros_like(self.arena_image).astype(np.uint8)
        self.arena_with_mask_image = np.zeros_like(
            self.arena_image).astype(np.uint8)

        self.arena_image_label = QLabel()
        self.mask_image_label = QLabel()
        self.arena_with_mask_image_label = QLabel()

        self.update_arena_image_label()
        self.update_mask_image_label()
        self.update_arena_with_mask_image_label()

        layout.addWidget(self.arena_image_label)
        layout.addWidget(self.mask_image_label)
        layout.addWidget(self.arena_with_mask_image_label)
        self.mask_image_groupbox.setLayout(layout)

    def _get_global_point_locations(self):
        """Returns global central point and mask point locations in image
        (pixel) coordinates."""
        central_rs, central_cs = 0, 0
        global_point_pos = np.zeros(shape=(len(self.mask_points), 2))
        # collect all of the mask points, generate global coords,
        # and find the center of mass of the points (center of the arena).
        for i, mask_point in enumerate(self.mask_points):
            # transform coords w.r.t. graphics_scene_pixmap
            point_pos = np.array([mask_point.y(), mask_point.x()])
            global_point_pos[i, :] = (
                np.array([mask_point.ellipse_y, mask_point.ellipse_x]) +
                point_pos
                )
            central_rs += global_point_pos[i, 0]
            central_cs += global_point_pos[i, 1]

        central_point = np.array([
            central_rs / global_point_pos.shape[0],
            central_cs / global_point_pos.shape[0]])

        return central_point, global_point_pos

    @pyqtSlot()
    def load_mask(self):
        file_dialog = QFileDialog(self)
        mask_filename = str(file_dialog.getOpenFileName(
            caption='Open Mask File',
            filter='Spreadsheet (*.xlsx)'
            ))
        if mask_filename != '':
            self.tracking_settings.inclusion_mask_filename = mask_filename

        mask_df = pd.read_excel(mask_filename)
        for i, mask_point in enumerate(self.mask_points):
            mask_point.setPos(
                mask_df['cc'][i], mask_df['rr'][i])

    @pyqtSlot()
    def save_mask(self):
        """Save the position of each of the mask points into an .xlsx file.

        This will save two files: (1) the first contains the relative
        positions of the mask points, and is for use when loading a mask
        through the GUI. (2) The second file (named the same as the first
        with the addition of '-pixel-coords'), contains the 'true' positions
        of the mask points in pixel coordinates. This is for use in analyzing
        the positions of the tracking data (in analysis.py).
        """
        file_dialog = QFileDialog(self)
        mask_savefile = str(file_dialog.getSaveFileName(
            caption='Save Mask File',
            filter='Spreadsheet (*.xlsx)'
            ))
        if mask_savefile != '':
            self.tracking_settings.inclusion_mask_filename = mask_savefile
        else:
            return

        df = pd.DataFrame()
        rr, cc = [], []
        for mask_point in self.mask_points:
            rr.append(mask_point.y())
            cc.append(mask_point.x())

        df['rr'] = rr
        df['cc'] = cc
        df.to_excel(mask_savefile, index_label='node')

        # also save a file containing the global positions of the
        # arena mask coordinates -- for analysis of tracking data.
        central_point, global_point_pos = self._get_global_point_locations()
        df = pd.DataFrame()
        df['rr'] = global_point_pos[:, 0]
        df['cc'] = global_point_pos[:, 1]
        global_mask_savefile = mask_savefile[:-5] + '-pixel-coords.xlsx'
        df.to_excel(global_mask_savefile, index_label='node')

    @pyqtSlot()
    def generate_mask(self):
        # get the center of mass of all mask points, and all of the individual
        # mask point locations in pixel coordinates.
        central_point, global_point_pos = self._get_global_point_locations()

        # get coordinates such that they are all relative to the central point
        relative_point_pos = global_point_pos - central_point
        # sort the mask_points based on angle made with center of image.
        angles = np.arctan2(relative_point_pos[:, 0], relative_point_pos[:, 1])
        sorted_polygon_points = relative_point_pos[np.argsort(angles)]

        # place coordinates back into global positions for mask drawing.
        sorted_polygon_points += central_point
        # add first point onto end of points list to form closed polygon
        sorted_polygon_points = np.vstack((sorted_polygon_points,
            sorted_polygon_points[-1, :]))
        mask = np.zeros_like(self.arena_image)
        rr, cc = polygon(sorted_polygon_points[:, 0],
            sorted_polygon_points[:, 1], shape=self.arena_image.shape)
        mask[rr, cc] = 1
        # set this mask as the inclusion mask in our tracking_settings dict.
        self.tracking_settings.inclusion_mask = mask

        self.mask_image = convert_img_to_uint8(mask)

        self.arena_with_mask_image = self.arena_image.copy()
        self.arena_with_mask_image[~mask.astype(np.bool)] = 0

        self.update_mask_image_label()
        self.update_arena_with_mask_image_label()

    def update_arena_image_label(self):
        self.arena_image_label.setPixmap(
            QPixmap.fromImage(get_q_image(self.arena_image))
        )

    def update_mask_image_label(self):
        # TODO: update mask here.
        self.mask_image_label.setPixmap(
            QPixmap.fromImage(get_q_image(self.mask_image))
        )

    def update_arena_with_mask_image_label(self):
        # TODO: update arena_with_mask_image here
        self.arena_with_mask_image_label.setPixmap(
            QPixmap.fromImage(get_q_image(self.arena_with_mask_image))
        )
